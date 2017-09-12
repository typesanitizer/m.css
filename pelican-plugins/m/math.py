import re

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.parsers.rst.roles import set_classes

from . import latex2svg

latex2svg_params = latex2svg.default_params.copy()
latex2svg_params.update({
    # Don't use libertine fonts as they mess up things
    'preamble': r"""
\usepackage[utf8x]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{newtxtext}
""",
    # Zoom the letters a bit to match page font size
    'dvisvgm_cmd': 'dvisvgm --no-fonts -Z 1.25',
    })

uncrap_src = re.compile(r"""<\?xml version='1.0' encoding='UTF-8'\?>
<!-- This file was generated by dvisvgm \d+\.\d+\.\d+ -->
<svg (?P<attribs>.+) xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>
""")

uncrap_dst = r"""<svg{attribs} \g<attribs>>
<title>LaTeX Math</title>
<description>
{formula}
</description>
"""

class Math(rst.Directive):
    option_spec = {'class': directives.class_option,
                   'name': directives.unchanged}
    has_content = True

    def run(self):
        set_classes(self.options)
        self.assert_has_content()
        # join lines, separate blocks
        content = '\n'.join(self.content).split('\n\n')
        _nodes = []
        for block in content:
            if not block:
                continue

            container = nodes.container(**self.options)
            container['classes'] += ['m-math']
            node = nodes.raw(self.block_text, uncrap_src.sub(
                uncrap_dst.format(attribs='', formula=block.replace('\\', '\\\\')),
                latex2svg.latex2svg("$$" + block + "$$", params=latex2svg_params)['svg']), format='html')
            node.line = self.content_offset + 1
            self.add_name(node)
            container.append(node)
            _nodes.append(container)
        return _nodes

def math(role, rawtext, text, lineno, inliner, options={}, content=[]):
    # Otherwise the backslashes do quite a mess there
    i = rawtext.find('`')
    text = rawtext.split('`')[1]

    # Apply classes to the <svg> element instead of some outer <span>
    set_classes(options)
    classes = 'm-math'
    if 'classes' in options:
        classes += ' ' + ' '.join(options['classes'])
        del options['classes']

    out = latex2svg.latex2svg("$" + text + "$", params=latex2svg_params);

    # CSS classes and styling for proper vertical alignment. Depth is relative
    # to font size, describes how below the line the text is. Scaling it back
    # to 12pt font, scaled by 125% as set above in the config.
    attribs = ' class="{}" style="vertical-align: -{:.1f}pt;"'.format(classes, out['depth']*12*1.25)

    node = nodes.raw(rawtext, uncrap_src.sub(
        uncrap_dst.format(attribs=attribs, formula=text.replace('\\', '\\\\')),
        out['svg']), format='html', **options)
    return [node], []

def register():
    rst.directives.register_directive('math', Math)
    rst.roles.register_canonical_role('math', math)