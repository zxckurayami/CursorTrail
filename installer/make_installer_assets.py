import struct
import sys
import zlib


ICON_SIZES = (256, 128, 64, 48, 32, 16)


def read_source_icon(path):
    data = open(path, "rb").read()
    reserved, icon_type, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0 or icon_type != 1 or count < 1:
        raise ValueError("Unsupported ICO file.")

    candidates = []
    for index in range(count):
        offset = 6 + 16 * index
        width_byte, height_byte, _, _, _, bit_count, size, image_offset = struct.unpack_from("<BBBBHHII", data, offset)
        width = 256 if width_byte == 0 else width_byte
        height = 256 if height_byte == 0 else height_byte
        candidates.append((width * height, bit_count, width, height, image_offset, size))

    candidates.sort(reverse=True)
    _, bit_count, _, _, image_offset, _ = candidates[0]
    if bit_count != 32:
        raise ValueError("Only 32-bit ICO images are supported.")

    header_size = struct.unpack_from("<I", data, image_offset)[0]
    if header_size != 40:
        raise ValueError("Only BITMAPINFOHEADER ICO images are supported.")

    _, width, dib_height, _, bpp, _, _, _, _, _, _ = struct.unpack_from("<IiiHHIIiiII", data, image_offset)
    if bpp != 32:
        raise ValueError("Only 32-bit ICO images are supported.")

    height = dib_height // 2
    pixels_offset = image_offset + header_size
    pixels = []
    stride = width * 4
    for y in range(height):
        row_offset = pixels_offset + (height - 1 - y) * stride
        row = []
        for x in range(width):
            b, g, r, a = data[row_offset + x * 4:row_offset + x * 4 + 4]
            row.append((r, g, b, a))
        pixels.append(row)
    return width, height, pixels


def make_square_canvas(width, height, pixels, size):
    canvas = [[(0, 0, 0, 0) for _ in range(size)] for _ in range(size)]
    scale = min(float(size) / width, float(size) / height)
    target_w = max(1, int(round(width * scale)))
    target_h = max(1, int(round(height * scale)))
    resized = resize_rgba(width, height, pixels, target_w, target_h)
    ox = (size - target_w) // 2
    oy = (size - target_h) // 2
    for y in range(target_h):
        for x in range(target_w):
            canvas[oy + y][ox + x] = resized[y][x]
    return canvas


def resize_rgba(width, height, pixels, target_w, target_h):
    if width == target_w and height == target_h:
        return [row[:] for row in pixels]

    result = []
    for y in range(target_h):
        source_y = (y + 0.5) * height / target_h - 0.5
        y0 = max(0, min(height - 1, int(source_y)))
        y1 = max(0, min(height - 1, y0 + 1))
        wy = source_y - y0
        row = []
        for x in range(target_w):
            source_x = (x + 0.5) * width / target_w - 0.5
            x0 = max(0, min(width - 1, int(source_x)))
            x1 = max(0, min(width - 1, x0 + 1))
            wx = source_x - x0
            c00 = pixels[y0][x0]
            c10 = pixels[y0][x1]
            c01 = pixels[y1][x0]
            c11 = pixels[y1][x1]
            row.append(tuple(
                int(round(
                    c00[channel] * (1 - wx) * (1 - wy) +
                    c10[channel] * wx * (1 - wy) +
                    c01[channel] * (1 - wx) * wy +
                    c11[channel] * wx * wy
                ))
                for channel in range(4)
            ))
        result.append(row)
    return result


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_png(path, size, pixels):
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b, a in row:
            raw.extend((r, g, b, a))

    png = bytearray()
    png.extend(b"\x89PNG\r\n\x1a\n")
    png.extend(png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)))
    png.extend(png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
    png.extend(png_chunk(b"IEND", b""))
    open(path, "wb").write(png)


def dib_for_icon(size, pixels):
    header = struct.pack("<IiiHHIIiiII", 40, size, size * 2, 1, 32, 0, size * size * 4, 0, 0, 0, 0)
    xor = bytearray()
    for y in range(size - 1, -1, -1):
        for r, g, b, a in pixels[y]:
            xor.extend((b, g, r, a))

    mask_stride = ((size + 31) // 32) * 4
    and_mask = b"\x00" * (mask_stride * size)
    return header + bytes(xor) + and_mask


def write_ico(path, base_pixels):
    images = []
    for size in ICON_SIZES:
        resized = resize_rgba(256, 256, base_pixels, size, size)
        images.append((size, dib_for_icon(size, resized)))

    directory_size = 6 + 16 * len(images)
    image_offset = directory_size
    header = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    image_data = bytearray()
    for size, payload in images:
        width_byte = 0 if size == 256 else size
        height_byte = 0 if size == 256 else size
        header.extend(struct.pack("<BBBBHHII", width_byte, height_byte, 0, 0, 1, 32, len(payload), image_offset))
        image_data.extend(payload)
        image_offset += len(payload)

    open(path, "wb").write(header + image_data)


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: make_installer_assets.py source.ico logo.png setup.ico")

    source_icon, logo_png, setup_icon = sys.argv[1:]
    width, height, pixels = read_source_icon(source_icon)
    square = make_square_canvas(width, height, pixels, 256)
    write_png(logo_png, 256, square)
    write_ico(setup_icon, square)


if __name__ == "__main__":
    main()
