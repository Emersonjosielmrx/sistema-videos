import functions_framework

@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function de exemplo."""
    name = request.args.get("name", "World")
    return f"Hello {name}! (Inovare Cloud Function)"
