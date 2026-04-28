import logging
from pygments.lexers import get_lexer_by_name
from pygments.lexer import RegexLexer
from pygments.token import Keyword, Name, String, Number, Comment, Operator, Punctuation, Whitespace, Token
from pygments.styles import get_style_by_name
from rich.text import Text

logger = logging.getLogger(__name__)

# Theme name: configurable per user preference
THEME = "zenburn"  # Default theme, can be changed via set_theme()

# Cache for style lookups
_style_cache = {}


class GoTemplateLexer(RegexLexer):
    """Lexer for Go text/html templates with YAML."""
    name = "Go Template"
    aliases = ["gotmpl"]
    filenames = ["*.tpl"]

    tokens = {
        "root": [
            (r"\{\{-?", Punctuation),
            (r"-?\}\}", Punctuation),
            (r"\b(if|else|end|range|define|template|block|with)\b", Keyword),
            (r"\b(and|or|not|eq|ne|lt|le|gt|ge|call|html|js|index|len|slice|print|printf|println|urlquery)\b", Name.Builtin),
            (r"\$\w+", Name.Variable),
            (r"\.\w+", Name.Attribute),
            (r"\"[^\"]*\"", String.Double),
            (r"'[^']*'", String.Single),
            (r"-?\d+\.\d+", Number.Float),
            (r"-?\d+", Number.Integer),
            (r"\b(true|false|nil)\b", Keyword.Constant),
            (r"[|:=]", Operator),
            (r"#.*$", Comment.Single),
            (r"\s+", Whitespace),
            (r".", Whitespace),
        ]
    }


def _get_rich_style(token_type) -> str:
    """Map Pygments token type to Rich style using theme."""
    if token_type in _style_cache:
        return _style_cache[token_type]

    try:
        style_obj = get_style_by_name(THEME)
        style_dict = style_obj.style_for_token(token_type)

        # Convert Pygments style to Rich style string
        parts = []
        if style_dict["bold"]:
            parts.append("bold")
        if style_dict["italic"]:
            parts.append("italic")
        if style_dict["underline"]:
            parts.append("underline")
        if style_dict["color"]:
            parts.append(f"#{style_dict['color']}")

        rich_style = " ".join(parts) if parts else "white"
        _style_cache[token_type] = rich_style
        return rich_style
    except Exception:
        _style_cache[token_type] = "white"
        return "white"


def _tokens_to_rich(tokens: list) -> Text:
    """Convert Pygments tokens to Rich.Text object using current theme."""
    text = Text()

    for token_type, value in tokens:
        style = _get_rich_style(token_type)
        if value.strip():
            text.append(value, style=style)
        else:
            text.append(value)

    return text


def highlight_yaml(content: str) -> Text:
    """Syntax highlight YAML using Pygments."""
    try:
        lexer = get_lexer_by_name("yaml")
        tokens = list(lexer.get_tokens(content))
        return _tokens_to_rich(tokens)
    except Exception as e:
        logger.warning(f"YAML highlighting failed: {e}")
        return Text(content)


def highlight_go_template(content: str) -> Text:
    """Syntax highlight Go template using Pygments."""
    try:
        lexer = GoTemplateLexer()
        tokens = list(lexer.get_tokens(content))
        return _tokens_to_rich(tokens)
    except Exception as e:
        logger.warning(f"Go template highlighting failed: {e}")
        return Text(content)


def set_theme(theme_name: str) -> None:
    """Set syntax highlighting theme. Available: monokai, dracula, nord, etc."""
    global THEME
    try:
        get_style_by_name(theme_name)
        THEME = theme_name
        _style_cache.clear()
        logger.debug(f"Switched to theme: {theme_name}")
    except Exception as e:
        logger.error(f"Theme '{theme_name}' not found: {e}")


def get_theme() -> str:
    """Get current syntax highlighting theme."""
    return THEME
