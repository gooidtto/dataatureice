def toggle_favorite(app, row):
    """Toggle one result-row favorite using the shared content identity service."""
    if not row:
        return False
    if app.fav.has(row):
        app.fav.remove([row])
        if hasattr(app, 'rows'):
            app.render(app.rows)
        if hasattr(app, 'toast'):
            app.toast('已移除收藏')
        return False
    app.addToFavorites([row])
    return True
