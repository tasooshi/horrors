import string


class Template:

    template_path = None
    template_context = None

    def __init__(self, config):
        self.config = config
        with open(self.template_path, 'r') as fil:
            self.source = fil.read()

    def preprocess(self, template):
        return template

    def generate(self, request_context):
        # FIXME: Optimize
        context = self.template_context.copy()
        for key, val in context.items():
            context[key] = string.Template(val).substitute(request_context)
        template = string.Template(self.source).substitute(context)
        output = self.preprocess(template)
        return output
