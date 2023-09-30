def generate_nav_link(path, value):
    if request.url.path == value:
        return 'class="nav-link active" aria-current="page"'
    else:
        return 'class="nav-link text-white"'
