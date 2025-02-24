#!/usr/bin/env python3

from scipy.special import binom

from plot import hist


def main():

    x = list(range(3, 14))
    k3n5_y = {f"N={N}": [100 * prob(M, 5, 3, N) for M in x] for N in range(10, 51, 10)}

    hist(x, k3n5_y, title="Probability of Hijacking Cloud Deployment (k=3, n=5)", xlabel="# hijackable vantage points", ylabel="% prob. success", overlay=True, ylim=(0,6))

    k7n9_y = {f"N={N}": 4 * [0] + [100 * prob(M, 9, 7, N) for M in x[-7:]] for N in range(10, 51, 10)}
    hist(x, k7n9_y, title="Probability of Hijacking Cloud Deployment (k=7, n=9)", xlabel="# hijackable vantage points", ylabel="% prob. success", overlay=True, ylim=(0,6))

    hist(x=["k=3", "k=5", "k=7"], y={"LE": [0.511, 0.518, 0.514], "LE DNS": [0.417, 0.420, 0.419], "TOR": [0.265, 0.235, 0.247], "TOR DNS": [0.250, 0.247, 0.246], "AWS30": [0.230, 0.255, 0.263], "AWS30 DNS": [0.204, 0.229, 0.240]}, title="Path Overlap", xlabel="# validators", ylabel="path overlap", ylim=(0, 1), style={"LE": (None, "#555c9d"), "LE DNS": ("///", "#555c9d"), "TOR": (None, "#ff8c78"), "TOR DNS": ("///", "#ff8c78"), "AWS30": (None, "#842c61"), "AWS30 DNS": ("///", "#842c61")})



def prob(M: int, n: int, k: int, N: int):
    return sum(binom(k, j) * (M / N) ** k * (1 - M / N) ** (k - j) for j in range(k - (n - k), k + 1))


def hypergeom(M: int, n: int, k: int, N: int):
    return binom(M, k) * binom(N - M, n - k) / binom(N, n)


if __name__ == '__main__':
    main()
