import json
import glob
import os


def validate_dict_fields(expectedDict, ActualDict):
    assert set(expectedDict.keys()) == set(ActualDict.keys()
                                           ), "Keys mismatch between expected and Actual data"

    # Check if values for each key match
    for key in expectedDict:
        assert expectedDict[key] == ActualDict[
            key], f"Values for key '{key}' do not match: {expectedDict[key]} != {ActualDict[key]}\n{ActualDict}"


def validate_is_sorted(ids, sortOrder='|asc'):
    if ids == []:
        raise ValueError("empty ids provided")
    if sortOrder == '|asc':
        return all(ids[i] <= ids[i + 1] for i in range(len(ids) - 1))
    elif sortOrder == '|desc':
        return all(ids[i] >= ids[i + 1] for i in range(len(ids) - 1))
    else:
        raise ValueError("Order must be either 'asc' or 'desc'")


def split_Json(input_file, output_dir, chunk_size=100):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the entire JSON file
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Delete the old files

    files = glob.glob(os.path.join(output_dir, '*'))

    for file in files:
        try:
            os.remove(file)
            print(f"Deleted file: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

    # Ensure the data is a list
    if not isinstance(data, list):
        raise ValueError("The JSON file does not contain a list of objects")

    # Split the data into chunks
    total_chunks = len(data)
    chunkNo = 0

    for i in range(0, total_chunks, chunk_size):
        chunk = data[i:i + chunk_size]
        filtered_chunk = [entry for entry in chunk if entry.get(
            "kb", {}).get("id") is not None]

        # remove duplicates can be done
        output_file = os.path.join(output_dir, f"chunk_{chunkNo + 1}.json")
        chunkNo += 1
        with open(output_file, 'w', encoding='utf-8') as out_file:
            json.dump(filtered_chunk, out_file, ensure_ascii=False, indent=4)
        print(f"Chunk {chunkNo} written to {output_file}")
