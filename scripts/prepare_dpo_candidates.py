#!/usr/bin/env python3
"""Prepare a bounded source-preference review set; never silently approve DPO data."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from triage_poc.anonymization import TextAnonymizer
from triage_poc.comparison import sha256
from triage_poc.dpo import prompt_hash, validate_preferences
from triage_poc.source_sft import SOURCE_DIRECT_IDENTIFIER_ENTITIES
from triage_poc.source_sft_preflight import validate_source_sft_artifacts
from triage_poc.ultramedical_audit import _iter_split, normalize_text
from triage_poc.ultramedical_rebuild import _preference_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--sft-artifacts", required=True, type=Path)
    parser.add_argument("--sft-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--train-count", type=int, default=512)
    parser.add_argument("--validation-count", type=int, default=64)
    args = parser.parse_args()
    if args.output.exists() or min(args.train_count, args.validation_count) < 1:
        raise ValueError("Use positive quotas and a fresh output directory.")
    root = Path(__file__).resolve().parents[1]
    source_path = root / 'data/manifests/src-ultramedical-preference-761eb79.json'
    source = json.loads(source_path.read_text())
    index_manifest = json.loads(
        (root / 'data/manifests/derived-ultramedical-reconstruction-v1.json').read_text())
    if sha256(args.index) != index_manifest['artifact']['sha256']:
        raise ValueError("Reconstruction index checksum mismatch.")
    # Verify opaque bytes of the pinned source, without using test answers for selection.
    digest = hashlib.sha256()
    for split in ('train', 'dev', 'test'):
        with (args.source / f'{split}.json').open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
    if digest.hexdigest() != source['artifact']['sha256']:
        raise ValueError("Source version checksum mismatch.")
    _, canonical, _, _ = validate_source_sft_artifacts(
        args.sft_manifest, args.sft_artifacts, audit_candidate=True)
    # Exclude all SFT prompts, including validation/test; no QA answer is used here.
    protected = {prompt_hash(r['instruction']) for r in canonical}
    index = {'train': {}, 'dev': {}}
    for line in args.index.read_text().splitlines():
        item = json.loads(line)
        if item['decision'] == 'reserved_evaluation':
            protected.add(item['prompt_group_sha256'])
        if item['decision'] in {'candidate_training', 'candidate_validation'}:
            index[item['source_split']][item['source_row_index']] = item
    seen = set(protected)
    anonymizer = TextAnonymizer(entities=SOURCE_DIRECT_IDENTIFIER_ENTITIES)
    rows = {'train': [], 'validation': []}
    excluded = Counter()
    for original, split, quota in [('dev', 'validation', args.validation_count),
                                    ('train', 'train', args.train_count)]:
        for position, row in enumerate(_iter_split(args.source / f'{original}.json')):
            item = index[original].get(position)
            if not item:
                continue
            if _preference_hash(row) != item['preference_sha256']:
                raise ValueError('Source row does not match the reconstruction index.')
            if prompt_hash(row['prompt']) in seen:
                excluded['protected_or_duplicate_prompt'] += 1
                continue
            conversations = [row['chosen'], row['rejected']]
            if any([m.get('role') for m in c] != ['user', 'assistant'] for c in conversations):
                excluded['unsupported_conversation'] += 1
                continue
            if any(normalize_text(c[0]['content']) != normalize_text(row['prompt'])
                   for c in conversations):
                excluded['conversation_prompt_mismatch'] += 1
                continue
            texts = [row['prompt']] + [c[1]['content'] for c in conversations]
            if any(not t.strip() or len(t) > 6000 for t in texts):
                excluded['length_or_empty'] += 1
                continue
            cleaned = [anonymizer.anonymize(t, 'en') for t in texts]
            if any(r.audit.status != 'passed' for r in cleaned):
                excluded['pii_review_required'] += 1
                continue
            prompt, chosen, rejected = [r.text for r in cleaned]
            if prompt_hash(prompt) in seen or normalize_text(chosen) == normalize_text(rejected):
                excluded['post_anonymization_duplicate'] += 1
                continue
            seen.update([prompt_hash(row['prompt']), prompt_hash(prompt)])
            rows[split].append({
                'record_id': f'ultramedical-{original}-{position}', 'split': split,
                'language': 'en', 'prompt': prompt, 'chosen': chosen, 'rejected': rejected,
                'preference_rationale': 'Source biomedical preference; project review pending.',
                'source_label_type': row['label_type'],
                'source': {'manifest_id': source['manifest_id'],
                           'license': source['license']['identifier'],
                           'revision': source['immutable_revision'],
                           'locator': f'{original}.json:{position}',
                           'preference_sha256': item['preference_sha256']},
                'pii_anonymization_status': 'passed_direct_identifiers_only',
                'clinical_review_status': 'not_performed',
                'project_review_status': 'pending',
            })
            if len(rows[split]) % 16 == 0:
                print(f'{split}: {len(rows[split])}/{quota}', flush=True)
            if len(rows[split]) == quota:
                break
        if len(rows[split]) != quota:
            raise ValueError('Insufficient eligible source preferences for the requested quota.')
    validate_preferences(rows['train'], rows['validation'], protected, require_review=False)
    args.output.mkdir(parents=True)
    artifacts = {}
    for split, records in rows.items():
        path = args.output / f'{split}.jsonl'
        path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
        artifacts[split] = {'records': len(records), 'sha256': sha256(path)}
    manifest = {
        'status': 'candidate_review_required', 'clinical_review_status': 'not_performed',
        'artifacts': artifacts, 'source_manifest_id': source['manifest_id'],
        'source_revision': source['immutable_revision'], 'source_sha256': digest.hexdigest(),
        'index_sha256': sha256(args.index), 'script_sha256': sha256(Path(__file__)),
        'sft_manifest_sha256': sha256(args.sft_manifest),
        'sft_protected_records': len(canonical),
        'protected_prompt_hashes': sorted(protected), 'test_answers_used': 0,
        'excluded_counts': dict(excluded), 'language': 'en',
        'anonymization_entities': list(SOURCE_DIRECT_IDENTIFIER_ENTITIES),
        'selection': 'first eligible source rows in preserved order; validation before train',
        'limits': ['Biomedical preferences are not validated triage preferences.',
                   'Direct identifier scan only; contextual PII and content require review.',
                   'Exact normalized hashes do not establish semantic decontamination.',
                   'This English-only candidate set does not establish bilingual alignment.'],
    }
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
