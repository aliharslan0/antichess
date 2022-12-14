from re import findall, match

from chess import Board
from chess.engine import SimpleEngine, Limit
from chess.polyglot import open_reader
from playwright.sync_api import sync_playwright

ENGINE_PATH = ''
BOOK_PATH = ''
USERNAME = ''
PASSWORD = ''


def uci_to_coordinate(uci: str):
    _x1, _y1, _x2, _y2 = match(r'([a-h])([1-8])([a-h])([1-8])', uci).groups()
    return ord(_x1) - ord('a'), 8 - int(_y1), ord(_x2) - ord('a'), 8 - int(_y2)


def main():
    class Normal:
        @staticmethod
        def last_move():
            elm = page.query_selector('u8t:last-of-type')
            return elm.text_content() if elm else None

        @staticmethod
        def turn():
            elms = page.query_selector_all('l4x > u8t')
            return len(elms) % 2 == 0

        @staticmethod
        def flip():
            page.query_selector('.flip').click(delay=100)

        @staticmethod
        def in_match():
            return page.query_selector('rm6') is not None

        @staticmethod
        def wait_until_match():
            page.wait_for_selector('rm6')

    class Puzzle:
        @staticmethod
        def get_moves():
            moves = page.query_selector_all('move')
            return [i.text_content() for i in moves]

    def board_position():
        return page.query_selector('cg-board').bounding_box()

    def get_length():
        container = page.query_selector('cg-container').get_attribute('style')
        return int(findall(r'[0-9]+', container)[0]) // 8

    def get_orientation():
        orientation_class = page.query_selector('.cg-wrap').get_attribute('class')
        return findall(r'orientation-(white|black)', orientation_class)[0]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://lichess.org/login')
        page.fill('#form3-username', USERNAME)
        page.fill('#form3-password', PASSWORD)
        page.click('.one-factor > button:nth-child(3)')

        while (mode := input('[N] Normal match, [Q] Quit: ').lower().strip()) != 'q':
            if mode == 'n':
                Normal.wait_until_match()
                color = get_orientation() == 'white'
                board = Board()
                engine = SimpleEngine.popen_uci(ENGINE_PATH)
                book = open_reader(BOOK_PATH)

                if not color:
                    Normal.flip()
                    while not Normal.last_move():
                        pass

                table = board_position()
                length = get_length()
                middle = length // 2

                while not board.is_game_over():
                    if Normal.turn() == color:
                        lm = Normal.last_move()
                        if lm:
                            board.push_san(lm)

                        if board.is_game_over():
                            break

                        if opening := book.get(board):
                            move = opening.move
                        else:
                            move = engine.play(board, Limit(time=0.001)).move

                        coordinates = uci_to_coordinate(move.uci())
                        x1 = table['x'] + (length * coordinates[0]) + middle
                        y1 = table['y'] + (length * coordinates[1]) + middle
                        x2 = table['x'] + (length * coordinates[2]) + middle
                        y2 = table['y'] + (length * coordinates[3]) + middle

                        page.mouse.click(x1, y1, delay=100)
                        page.mouse.click(x2, y2, delay=100)
                        if move.promotion:
                            page.mouse.click(x2, y2, delay=100)

                        board.push(move)

                engine.close()
                book.close()


if __name__ == '__main__':
    main()
