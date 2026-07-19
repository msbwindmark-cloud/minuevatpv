SMARTLOOK_SCRIPT = """<script type='text/javascript'>
  window.smartlook||(function(d) {
    var o=smartlook=function(){ o.api.push(arguments)},h=d.getElementsByTagName('head')[0];
    var c=d.createElement('script');o.api=new Array();c.async=true;c.type='text/javascript';
    c.charset='utf-8';c.src='https://web-sdk.smartlook.com/recorder.js';h.appendChild(c);
    })(document);
    smartlook('init', '1c102b1307aaa4582cacfe5182120da4a2cc58d7', { region: 'eu' });
</script>"""


class SmartlookMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response

        if isinstance(response, bytes):
            return response

        content = response.content.decode('utf-8', errors='replace')

        if '</head>' in content:
            content = content.replace('</head>', SMARTLOOK_SCRIPT + '\n</head>', 1)
            response.content = content.encode('utf-8')
            if 'Content-Length' in response:
                del response['Content-Length']

        return response
