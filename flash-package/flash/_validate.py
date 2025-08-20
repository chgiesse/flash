from dash import exceptions
import quart


def validate_use_pages(config):
    if not config.get("assets_folder", None):
        raise exceptions.PageError(
            "`dash.register_page()` must be called after app instantiation"
        )

    if quart.has_request_context():
        raise exceptions.PageError(
            """
            dash.register_page() can’t be called within a callback as it updates dash.page_registry, which is a global variable.
             For more details, see https://dash.plotly.com/sharing-data-between-callbacks#why-global-variables-will-break-your-app
            """
        )
