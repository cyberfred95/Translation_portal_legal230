import os
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.views import View

_SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lexamt API - Documentation</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui.css">
  <style>
    body {{ margin: 0; }}
    #swagger-ui .topbar {{ background-color: #1a1a2e; }}
    #swagger-ui .topbar .download-url-wrapper {{ display: none; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function () {{
      SwaggerUIBundle({{
        url: "{yaml_url}",
        dom_id: '#swagger-ui',
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
        layout: "StandaloneLayout",
        deepLinking: true,
        persistAuthorization: true,
        displayRequestDuration: true,
        filter: true,
      }});
    }};
  </script>
</body>
</html>"""


class SwaggerUIView(View):
    def get(self, request):
        yaml_url = request.build_absolute_uri(reverse('api-swagger-yaml'))
        html = _SWAGGER_UI_HTML.format(yaml_url=yaml_url)
        return HttpResponse(html, content_type='text/html; charset=utf-8')


class SwaggerYAMLView(View):
    YAML_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'document', 'swagger.yaml'
    )

    def get(self, request):
        if not os.path.exists(self.YAML_PATH):
            raise Http404("swagger.yaml not found")
        with open(self.YAML_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/yaml')
