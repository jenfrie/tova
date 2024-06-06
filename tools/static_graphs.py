#!/usr/bin/env python3

from scipy.special import binom

from plot import hist, plt, line


def main():
    scenarios = [(3, 4), (5, 7), (7, 9)]
    N = 2254
    x = list(range(500))
    y = {f"k={k},n={n}": ([100 * prob(M, n, k, N) for M in x], [100 * sum(hypergeom(M, n, j, N) for j in range(k, n + 1)) for M in x]) for k, n in scenarios}

    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, (label, (real_prob, hg_dist)) in enumerate(y.items()):
        plt.plot(x, real_prob, color=colors[i], label=label)
    for i, (label, (real_prob, hg_dist)) in enumerate(y.items()):
        plt.plot(x, hg_dist, color=colors[i], linestyle="--", label="hypergeo")

    plt.ylim((0, max(x for rp, hg in y.values() for x in rp + hg)))
    plt.xlim((0, max(x)))
    plt.legend(ncol=2)
    plt.grid(axis="y", color="gainsboro")
    plt.gca().set_axisbelow(True)
    plt.tight_layout(pad=1.5)
    plt.ylabel("% fraudulent validation")
    plt.xlabel("# malicious nodes")
    plt.savefig("attack_success_with_malicious_nodes.pdf")
    plt.close()


    hist(x=["TOR", "LE"], y={"DNS resolvers": [174, 9], "validators": [280, 7]}, title="Validator Origins of Let's Encrypt and TOR Network", ylabel="# unique BGP origins", horizontal=True)

    hist(x=["k=3", "k=5", "k=7"], y={"LE": [0.589, 0.592, 0.589], "TOR": [0.476, 0.321, 0.258]}, title="Path Overlap", xlabel="# validators", ylabel="path overlap", ylim=(0, 1))

    hist(x=["k=3", "k=5", "k=7"], y={"LE": [0.541, 0.540, 0.541], "TOR": [0.472, 0.342, 0.276]}, title="Path Overlap DNS", xlabel="# validators", ylabel="path overlap", ylim=(0, 1))

    path_overlap_hist_le_k3 = {"70.0": 3814, "30.0": 16108, "100.0": 8215}
    path_overlap_hist_le_k5 = {"100.0": 8035, "30.0": 15362, "70.0": 3695}
    path_overlap_hist_le_k7 = {"70.0": 3514, "30.0": 14984, "100.0": 7701}
    path_overlap_hist_tor_k3 = {"30.0": 29520, "70.0": 6185, "100.0": 4085}
    path_overlap_hist_tor_k5 = {"20.0": 42572, "60.0": 4482, "40.0": 7896, "100.0": 2540, "80.0": 2176}
    path_overlap_hist_tor_k7 = {"70.0": 1809, "10.0": 48209, "30.0": 7969, "40.0": 5404, "100.0": 2139, "60.0": 3381, "90.0": 752, "20.0": 1}

    x = [str(p) for p in range(0, 101, 10)]
    y_k3 = {"LE": [path_overlap_hist_le_k3.get(p + ".0", 0) for p in x],
            "TOR (k=3)": [path_overlap_hist_tor_k3.get(p + ".0", 0) for p in x]}
    y_k5 = {"LE": [path_overlap_hist_le_k5.get(p + ".0", 0) for p in x],
            "TOR (k=5)": [path_overlap_hist_tor_k5.get(p + ".0", 0) for p in x]}
    y_k7 = {"LE": [path_overlap_hist_le_k7.get(p + ".0", 0) for p in x],
            "TOR (k=7)": [path_overlap_hist_tor_k7.get(p + ".0", 0) for p in x]}
    hist(x=x, y=y_k3, title="Histogram of Path Overlap with 3 Validators", xlabel="% intercepted validators", ylabel="# ASes * # domains")
    hist(x=x, y=y_k5, title="Histogram of Path Overlap with 5 Validators", xlabel="% intercepted validators", ylabel="# ASes * # domains")
    hist(x=x, y=y_k7, title="Histogram of Path Overlap with 7 Validators", xlabel="% intercepted validators", ylabel="# ASes * # domains")


    path_overlap_hist_dns_le_k3 = {'30.0': 20514.2, '70.0': 4693.8, '100.0': 6345.4}
    path_overlap_hist_dns_le_k5 = {'100.0': 6150.4, '30.0': 19976.0, '70.0': 4513.0}
    path_overlap_hist_dns_le_k7 = {'100.0': 5922.0, '30.0': 19229.8, '70.0': 4383.0}
    path_overlap_hist_dns_tor_k3 = {'70.0': 6782.6, '30.0': 26285.0, '100.0': 3003.2}
    path_overlap_hist_dns_tor_k5 = {'20.0': 31709.6, '60.0': 4679.6, '40.0': 9065.6, '80.0': 2204.0, '100.0': 1647.8, '50.0': 472.6, '70.0': 8.6, '30.0': 20.4}
    path_overlap_hist_dns_tor_k7 = {'70.0': 2006.0, '10.0': 32131.4, '30.0': 8888.6, '20.0': 4989.0, '50.0': 761.4, '40.0': 5045.0, '60.0': 3216.4, '100.0': 1232.0, '90.0': 628.6, '80.0': 160.2}

    x = [str(p) for p in range(0, 101, 10)]
    y_k3 = {"LE": [path_overlap_hist_dns_le_k3.get(p + ".0", 0) for p in x],
            "TOR (k=3)": [path_overlap_hist_dns_tor_k3.get(p + ".0", 0) for p in x]}
    y_k5 = {"LE": [path_overlap_hist_dns_le_k5.get(p + ".0", 0) for p in x],
            "TOR (k=5)": [path_overlap_hist_dns_tor_k5.get(p + ".0", 0) for p in x]}
    y_k7 = {"LE": [path_overlap_hist_dns_le_k7.get(p + ".0", 0) for p in x],
            "TOR (k=7)": [path_overlap_hist_dns_tor_k7.get(p + ".0", 0) for p in x]}
    hist(x=x, y=y_k3, title="Histogram of DNS Path Overlap with 3 Validators", xlabel="% intercepted DNS resolvers", ylabel="# ASes * # domains")
    hist(x=x, y=y_k5, title="Histogram of DNS Path Overlap with 5 Validators", xlabel="% intercepted DNS resolvers", ylabel="# ASes * # domains")
    hist(x=x, y=y_k7, title="Histogram of DNS Path Overlap with 7 Validators", xlabel="% intercepted DNS resolvers", ylabel="# ASes * # domains")

    x = list(range(50))
    p = {f"k={k}": [binom(n, k) if n >= k else None for n in x] for k in [3, 5, 7]}
    line(x, p, title="binomial function", xlabel="n", ylabel="n over k", logscaley=True)


def prob(M: int, n: int, k: int, N: int):
    return sum(binom(k, j) * (M / N) ** k * (1 - M / N) ** (k - j) for j in range(k - (n - k), k + 1))


def hypergeom(M: int, n: int, k: int, N: int):
    return binom(M, k) * binom(N - M, n - k) / binom(N, n)


if __name__ == '__main__':
    main()
