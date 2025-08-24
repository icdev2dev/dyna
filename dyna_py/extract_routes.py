import re

HTTP_METHODS = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']

def extract_routes(filename):
    with open(filename, "r") as f:
        code = f.read()

    # Pattern for classic @app.route
    route_pattern = re.compile(r"@app\.route\(([^)]*)\)\s*def\s+([a-zA-Z0-9_]+)[(]")
    # Patterns for shortcut decorators @app.post("/foo") etc
    shortcut_patterns = {
        meth: re.compile(rf"@app\.{meth}\(\s*['\"]([^'\"]+)['\"]\s*\)\s*def\s+([a-zA-Z0-9_]+)[(]")
        for meth in HTTP_METHODS
    }

    output = []

    # Classic @app.route decorators
    for (route_args, func_name) in route_pattern.findall(code):
        # Find HTTP methods if specified, else default to GET
        m = re.search(r"methods\s*=\s*\[([^\]]+)\]", route_args)
        if m:
            methods = [s.strip().strip("'\"") for s in m.group(1).split(",")]
        else:
            methods = ["GET"]
        # Grab just the route string
        route_match = re.search(r'["\']([^"\']+)["\']', route_args)
        route = route_match.group(1) if route_match else "<parse error>"
        output.append({
            "route": route,
            "func": func_name,
            "methods": methods,
        })

    # Shortcut decorators (e.g. @app.post('/api/foo'))
    for method, pattern in shortcut_patterns.items():
        for match in pattern.findall(code):
            route, func_name = match
            output.append({
                "route": route,
                "func": func_name,
                "methods": [method.upper()]
            })

    # Print in config-list format
    print("MAP_HTTP_FUNCS = [")
    for rec in output:
        print(f"    ['{rec['route']}', {rec['func']}, {rec['methods']}],")
    print("]")

if __name__ == "__main__":
    extract_routes("flask_test.py")