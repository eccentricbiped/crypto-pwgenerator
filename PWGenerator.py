from PIL import Image, ImageDraw, ImageFont
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip84, Bip44Coins, Bip44Changes
from dotenv import load_dotenv
import qrcode
import binascii
import os
import sys
import time

load_dotenv()

def create_paper_wallet(coin_type, base_img_path:str, num_wallets:int, in_passphrase:str, in_path:str, is_test:bool = False):


    if coin_type == Bip44Coins.BITCOIN:

        deploy_path_base: str = "btc_" + str(int(time.time())) if not is_test else "btc_test_"

        if is_test:

            entropy_bytes_hex = str.encode(os.getenv("TEST_ENTROPY_BYTES"))
            entropy_mnemonic = Bip39MnemonicGenerator.FromEntropy(binascii.unhexlify(entropy_bytes_hex))
            create_and_deploy_bitcoin_wallet(base_img_path, entropy_mnemonic, in_passphrase, in_path, deploy_path_base)

        else:

            for n in range(0,num_wallets):
                bip_gen_mnemonic: str = Bip39MnemonicGenerator.FromWordsNumber(12)
                create_and_deploy_bitcoin_wallet(base_img_path, bip_gen_mnemonic, in_passphrase, in_path, deploy_path_base, n)



def create_and_deploy_bitcoin_wallet(base_img_path, bip_gen_mnemonic, in_passphrase, in_path, deploy_path_base, n=0):

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
    base_img.save(os.getenv("FILEBASE") + deploy_path_base + '_' + str(n) + ".png")

def main():

    # TODO: Currently only supports btc paper wallets
    if len(sys.argv) == 2: # PWGenerator.py num wallets (0 for test)
        if(sys.argv[1] == '0'):
            create_paper_wallet(Bip44Coins.BITCOIN, os.getenv("PAPER_WALLET_FRONT_PNG"), 1, os.getenv("PASSPHRASE"), os.getenv("BIP32_BIP43_PATH"), True)
        else:
            create_paper_wallet(Bip44Coins.BITCOIN, os.getenv("PAPER_WALLET_FRONT_PNG"), int(sys.argv[1]), os.getenv("PASSPHRASE"), os.getenv("BIP32_BIP43_PATH"))

if __name__ == '__main__':
    main()
