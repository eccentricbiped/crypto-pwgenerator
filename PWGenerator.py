from PIL import Image, ImageDraw, ImageFont
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip84, Bip44Coins, Bip44Changes
from dotenv import load_dotenv
import qrcode
import binascii
import os
import sys
import time
from reportlab.pdfgen.canvas import Canvas, PDFTextObject

load_dotenv()

def create_paper_wallet(coin_type, base_img_path:str, num_wallets:int, in_passphrase:str, in_path:str, is_test:bool = False):


    if coin_type == Bip44Coins.BITCOIN:

        deploy_path_base: str = "btc_" + str(int(time.time())) if not is_test else "btc_test_"

        if is_test:

            entropy_bytes_hex = str.encode(os.getenv("TEST_ENTROPY_BYTES"))
            entropy_mnemonic = Bip39MnemonicGenerator.FromEntropy(binascii.unhexlify(entropy_bytes_hex))
            create_and_deploy_bitcoin_wallet(base_img_path, entropy_mnemonic, in_passphrase, in_path, deploy_path_base)

        else:

            pdf_props:list = [ (5, 450), (5, 100) ]


            # Generate front-side wallets
            n:int = 0
            pdf_number:int = 0
            while n < num_wallets: #for n in range(0,num_wallets):

                img_paths: list = []

                for i in range(0, 2):
                    if n + i < num_wallets:
                        bip_gen_mnemonic: str = Bip39MnemonicGenerator.FromWordsNumber(12)
                        img_path = create_and_deploy_bitcoin_wallet(base_img_path, bip_gen_mnemonic, in_passphrase, in_path, deploy_path_base, n+i)
                        img_paths.append(img_path)
                    else:
                        break

                # Export to pdf
                pdf_path = os.getenv("FILEBASE_PDF") + deploy_path_base + "_" + str(pdf_number) + ".pdf"
                canvas = Canvas(pdf_path, pagesize=(612.0, 792.0))

                for i in range(0, len(img_paths)):
                    canvas.drawImage(img_paths[i], pdf_props[i][0], pdf_props[i][1], 600, 200)

                canvas.save()

                pdf_number += 1
                n += 2

            # Generate wallet back pdf
            pdf_path = os.getenv("FILEBASE_PDF") + "_back.pdf"
            canvas = Canvas(pdf_path, pagesize=(612.0, 792.0))
            pdf_back_text_pos: list = [(172, 545), (172, 195)] # need to tweak these based on num of characters since there's no obvious way to set center alignment

            # we know some glyphs are missing, suppress warnings
            import reportlab.rl_config
            reportlab.rl_config.warnOnMissingFontGlyphs = 0
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont('Impact', 'impact.ttf'))

            for i in range(0, 2):
                canvas.drawImage("./template/holiday_paper_wallet_back.png", pdf_props[i][0], pdf_props[i][1], 600, 200)

                text_obj:PDFTextObject = canvas.beginText()
                text_obj.setTextOrigin(pdf_back_text_pos[i][0], pdf_back_text_pos[i][1])
                text_obj.setFont("Impact", 14)
                text_obj.textOut("100,000")
                canvas.drawText(text_obj)

            canvas.save()









def create_and_deploy_bitcoin_wallet(base_img_path, bip_gen_mnemonic, in_passphrase, in_path, deploy_path_base, n=0) -> str:

    # Generate seed from in_passphrase
    seed_bytes = Bip39SeedGenerator(bip_gen_mnemonic).Generate(in_passphrase)

    # Generate BIP84 master keys
    bip_obj_mst = Bip84.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    bip_obj_acc = bip_obj_mst.Purpose().Coin().Account(0)
    bip_obj_change = bip_obj_acc.Change(Bip44Changes.CHAIN_EXT)

    # Generate mnemonic and base address
    mnemonic_seed = bip_gen_mnemonic.split()
    addr: str = bip_obj_change.AddressIndex(0).PublicKey().ToAddress()

    # Initialize drawing to  image
    base_img = Image.open(base_img_path)
    text_draw = ImageDraw.Draw(base_img)
    font = ImageFont.truetype(os.getenv("IMGFONT"), 48)

    # Draw mnemonic_seed to image
    for i in range(1, 13):
        x = 1839 if i <= 6 else 2430
        y_base = 280
        y = y_base + 80 * (i - 1) if i <= 6 else y_base + 80 * (i - 7)
        text: str = mnemonic_seed[i - 1]
        text_draw.text((x, y), text.upper(), font=font, fill="black", align="left")

    # Generate bech32 address QR code
    qr = qrcode.QRCode(box_size=9, border=2)
    qr.add_data(addr)
    qr.make(fit=True)
    qrc_img = qr.make_image()

    base_img.paste(qrc_img, (118, 350))

    # Draw address text and BIP32/BIP43 path info
    text = addr
    font = ImageFont.truetype(os.getenv("IMGFONT"), 32)
    text_draw.text((110, 129), text, font=font, fill="black", stroke_fill="white", stroke_width=5, align="left")
    text_draw.text((1839, 200), in_path + " with passphrase protection", font=font, fill="black", stroke_fill="white",
                   stroke_width=5, align="left")

    # Export image to deploy folder
    result_img_path = os.getenv("FILEBASE_PNG") + deploy_path_base + '_' + str(n) + ".png"
    base_img.save(result_img_path)

    return result_img_path


def main():

    # TODO: Currently only supports btc paper wallets
    if len(sys.argv) == 2: # PWGenerator.py num wallets (0 for test)
        if(sys.argv[1] == '0'):
            create_paper_wallet(Bip44Coins.BITCOIN, os.getenv("PAPER_WALLET_FRONT_PNG"), 1, os.getenv("PASSPHRASE"), os.getenv("BIP32_BIP43_PATH"), True)
        else:
            create_paper_wallet(Bip44Coins.BITCOIN, os.getenv("PAPER_WALLET_FRONT_PNG"), int(sys.argv[1]), os.getenv("PASSPHRASE"), os.getenv("BIP32_BIP43_PATH"))

if __name__ == '__main__':
    main()
