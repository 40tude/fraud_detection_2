# -----------------------------------------------------------------------------
g_Delivered_Records = 0


# -----------------------------------------------------------------------------
def ma_fonction() -> None:
    global g_Delivered_Records

    g_Delivered_Records += 1
    print(f"{g_Delivered_Records}")
    return


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    for i in range(5):
        ma_fonction()
