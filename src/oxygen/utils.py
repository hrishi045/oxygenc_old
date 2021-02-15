import sys


def error(text: str) -> None:
    print(u'\033[{}m{}\033[0m{}'.format("31;1", "[-] Error: ",
                                        ascii_to_utf8(text)), file=sys.stderr)
    sys.exit(1)


def warning(text: str) -> None:
    print(u'\033[{}m{}\033[0m{}'.format("33;1", "[!] Warning: ",
                                        ascii_to_utf8(text)), file=sys.stderr)


def successful(text: str) -> None:
    print(u'\033[{}m{}\033[0m{}'.format("32;1", "[+] Success: ",
                                        ascii_to_utf8(text)), file=sys.stderr)


def ascii_to_utf8(text: str) -> str:
    final_str = ""
    i = 0
    while i < len(text):
        if text[i] != "\\":
            final_str += text[i]
            i += 1
        else:
            current_unicode_char = "0x"
            for j in range(i + 3, i + 7):
                current_unicode_char += text[j].upper()
            final_str += chr(int(current_unicode_char, 16))
            i += 7

    return final_str
