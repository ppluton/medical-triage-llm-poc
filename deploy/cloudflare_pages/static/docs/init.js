window.addEventListener("DOMContentLoaded", () => {
  SwaggerUIBundle({
    url: "./openapi.json", dom_id: "#swagger-ui", deepLinking: true,
    supportedSubmitMethods: [], validatorUrl: null, persistAuthorization: false,
    defaultModelsExpandDepth: 0, docExpansion: "list",
  });
});
