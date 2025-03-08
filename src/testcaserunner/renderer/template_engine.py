from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Any

from ..defines import InternalError

RenderData = dict[str, Any]
class TemplateEngine:
    def __init__(self, template_dir: str) -> None:
        loader = FileSystemLoader(template_dir)
        self.environment = Environment(loader=loader)
    
    def render(self, template_name: str, data: RenderData) -> str:
        try:
            template = self.environment.get_template(template_name)
            return template.render(data)
        except TemplateNotFound as e:
            raise InternalError(f"Template not found: {e}")
        except Exception as e:
            raise InternalError(f"An error occurred while rendering the template: {e}")
