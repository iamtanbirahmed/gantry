import logging
from pygments.lexers import get_lexer_by_name
from pygments.lexer import RegexLexer
from pygments.token import Keyword, Name, String, Number, Comment, Operator, Punctuation, Whitespace
from rich.text import Text

logger = logging.getLogger(__name__)


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


def _tokens_to_rich(tokens: list) -> Text:
    """Convert Pygments tokens to Rich.Text object."""
    text = Text()
    token_styles = {
        Keyword: "bold cyan",
        Keyword.Constant: "bold magenta",
        Name.Builtin: "bold yellow",
        Name.Variable: "green",
        Name.Attribute: "magenta",
        String: "green",
        String.Double: "green",
        String.Single: "green",
        Number: "cyan",
        Number.Integer: "cyan",
        Number.Float: "cyan",
        Comment: "dim white",
        Comment.Single: "dim white",
        Operator: "white",
        Punctuation: "white",
    }

    for token_type, value in tokens:
        # Find style: check exact match, then parent types
        style = None
        for tok_type, rich_style in token_styles.items():
            if token_type == tok_type or token_type in tok_type:
                style = rich_style
                break

        if style and value.strip():
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
