import re
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.treeprocessors import etree

class AsideBlockProcessor(BlockProcessor):
    RE_FENCE_START = r'^ *!{3,} *\n' # start line, e.g., `   !!!! `
    RE_FENCE_END = r'\n *!{3,}\s*$'  # last non-blank line, e.g, '!!!\n  \n\n'
    counter = 0

    def test(self, parent, block):
        return re.match(self.RE_FENCE_START, block)

    def run(self, parent, blocks):
        original_block = blocks[0]
        blocks[0] = re.sub(self.RE_FENCE_START, '', blocks[0])

        # Find block with ending fence
        for block_num, block in enumerate(blocks):
            if re.search(self.RE_FENCE_END, block):
                # remove fence
                blocks[block_num] = re.sub(self.RE_FENCE_END, '', block)
                # render fenced area inside a new div
                e = etree.SubElement(parent, 'aside')
                e.set('style', f'--aside-counter: {self.counter}')
                self.parser.parseBlocks(e, blocks[0:block_num + 1])
                # remove used blocks
                for i in range(0, block_num + 1):
                    blocks.pop(0)
                self.counter += 1
                return True  # or could have had no return statement
        # No closing marker!  Restore and do nothing
        blocks[0] = original_block
        return False  # equivalent to our test() routine returning False

class AsideExtension(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(AsideBlockProcessor(md.parser), 'aside', 175)