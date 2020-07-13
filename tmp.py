import matplotlib.pyplot as plt

fp = open('debug/start.txt', 'r')
results = []
for line in fp.readlines():
    line = line.strip('\n')
    results.append(1 if line == 'True' else 0)

av = []
window_size = 100
for i in range(0, len(results), window_size):
    if i + window_size > len(results):
        continue
    av.append(sum(results[i:i+window_size]))

plt.plot(av)
plt.show()