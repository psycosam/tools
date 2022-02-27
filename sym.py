# Symbolize the new crash logs

import json
import argparse
import os
import sys
import subprocess


def get_dsym_from_dir(base_dir: str, image_name: str) -> str:
    if os.path.isdir(base_dir):
        contents = os.listdir(base_dir)
        for subpath in contents:
            if subpath.endswith(".dSYM") & os.path.isdir(os.path.join(base_dir, subpath)):
                dsym_path = os.path.join(base_dir, subpath, "Contents", "Resources", "DWARF", image_name)
                if os.path.isfile(dsym_path):
                    return dsym_path
    return ""


def get_image_dsym_info_from_loaded_images(loaded_images: list, sym_base_path: str) -> list:
    if not os.path.isdir(sym_base_path):
        return []

    images_info = []
    for image in loaded_images:
        if image['size'] != 0:
            uuid = image['uuid']
            sym_dir_path = os.path.join(sym_base_path, uuid)
            dsym_dict = {
                            'arch': image['arch'],
                            'path': image['path'],
                            'base': hex(image['base']),
                            'name': image['name']
                         }
            if os.path.isdir(sym_dir_path):
                dsym_dict['dsym_path'] = get_dsym_from_dir(sym_dir_path, image['name'])

            images_info.append(dsym_dict)
        else:
            images_info.append(None)

    return images_info


def symbolize(dsym_path, image_offset, arch):
    result = subprocess.run(['atos', '-arch', arch, '-o', dsym_path, "-l", "0", image_offset], stdout=subprocess.PIPE)
    result_str = result.stdout.decode('utf-8').rstrip()
    if result_str != image_offset:
        print(result_str)
        return True
    return False


def process_thread(thread, images_info):
    for frame_idx, frame in enumerate(thread['frames']):
        image_info = images_info[frame['imageIndex']]
        image_offset = hex(frame['imageOffset'])
        print(f"\t{frame_idx}", end=" ")
        if image_info is not None:
            if "dsym_path" in image_info:
                if not symbolize(image_info['dsym_path'], image_offset, image_info['arch']):
                    print(f"{image_offset}\t{image_info['name']}")
            else:
                print(f"{image_offset}\t{image_info['name']}")
        else:
            print(image_offset)


def main():
    parser = argparse.ArgumentParser(description="Symbolize the new crash stack from macOS 12 and onwards")
    parser.add_argument("-c", "--crash-log", help="Crash log file path", dest="crash_log", metavar="'CrashFilePath'",
                        required=True)
    parser.add_argument("-d", "--sym-dir", help="Path to directory containing the symbols", dest="sym_dir",
                        metavar="'SymbolsDir'", required=True)
    parser.add_argument("-o", "--out-file", help="Path to output file which will contain symbolized log, optional "
                                                 "- prints to stdout if not provided",
                        required=False, dest="out_file", metavar="'Output File Path'")

    args = parser.parse_args()

    sym_base_path = args.sym_dir
    if not os.path.isdir(sym_base_path):
        print("Symbols dir not found, exiting.")
        return
    sym_base_path = os.path.abspath(sym_base_path)
    # print(sym_base_path)

    with open(args.crash_log, 'r') as f:
        crash_log_data = f.read()

    if crash_log_data is not None:
        # Find the crash json from the dump
        app_info_idx = crash_log_data.find("}")
        json_end_idx = crash_log_data.rfind("}")
        json_data = crash_log_data[app_info_idx+1:json_end_idx+1]

        # Parse the json
        crash_data = json.loads(json_data)

        # Find the dsym corresponding to the loaded images
        loaded_images = crash_data['usedImages']
        images_info = get_image_dsym_info_from_loaded_images(loaded_images, sym_base_path)
        # pprint(images_info)

        if args.out_file is not None:
            sys.stdout = open(args.out_file, "w")

        # Start printing the crash info
        print(f"CPU Type: {crash_data['cpuType']}")
        print(f"Process Name: {crash_data['procName']}")
        print(f"Process Path: {crash_data['procPath']}")
        print(f"Version: {crash_data['bundleInfo']['CFBundleVersion']}")
        print(f"Process Uptime: {crash_data['uptime']}")
        print(f"Exception Info:")
        print(f"\tType: {crash_data['exception']['type']}")
        print(f"\tSub Type: {crash_data['exception']['subtype']}")
        print(f"\tTermination Reason: {crash_data['termination']['indicator']}")
        print(f"Crashing Thread: {crash_data['faultingThread']}")

        # Start processing each thread and print it's stack trace
        for thread_idx, thread in enumerate(crash_data['threads']):
            thread_name = ""
            if "name" in thread:
                thread_name = thread['name']
            elif "queue" in thread:
                thread_name = thread['queue']
            print(f"\nThread {thread_idx}: {thread_name}")
            process_thread(thread, images_info)

        if args.out_file is not None:
            sys.stdout.close()

    else:
        print("Error reading crash file. Exiting.")


if __name__ == "__main__":
    try:
        main()
    except OSError as er:
        print(er.args)
