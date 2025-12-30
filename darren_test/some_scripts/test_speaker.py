import sounddevice as sd

devices = sd.query_devices()
results: list[dict] = []

for idx, dev in enumerate(devices):
    name = dev["name"]

    results.append(dev)
cnt = 1   
for result in results:
    print("-" * 100)
    print(f"{cnt}. {result}")
    cnt += 1