import time
from datetime import datetime

import numpy
import pandas as pd
import pylab
from brownie import Contract, config, web3

test_mode = True
config["autofetch_sources"] = True
# controller = Contract("0x100daa78fc509db39ef7d04de0c1abd299f4c6ce") # wsteth
controller = Contract("0x4e59541306910ad6dc1dac0ac9dfb29bd9f15c67")  # wbtc
# controller = Contract('0x8472a9a7632b173c8cf3a86d3afec50c35548e76') # sfrxeth
# controller = Contract('0xa920de414ea4ab66b97da1bfe9e6eca7d4219635') # weth
amm = Contract(controller.amm())
custom_data_cols = 8

TEST_RESOLUTION = 10
PROD_RESOLUTION = 100


def get_users(conn, user_cap=None):
    if user_cap is None:
        print(f"Loading all loans for {conn}")
    else:
        print(f"Loading {user_cap} loans for {conn}")

    users = []
    if user_cap is None:
        user_cap = conn.n_loans()

    for i in range(user_cap):
        print(i)
        users.append(conn.loans(i))
    return users


def main():
    start_time = time.time()
    end_block = web3.eth.blockNumber
    start_block = 17432225
    counter = 0
    if test_mode:
        users = get_users(controller, 5)
    else:
        users = get_users(controller)

    pylab.figure(figsize=(20, 10))

    dataframe_data = []
    for user in users:
        print(f"{user} {counter} {time.time() - start_time:.2f} seconds elapsed")
        counter += 1
        times = []
        losses = []
        user_data = [[] for _ in range(custom_data_cols)]
        old_health = 0
        new_health = 0

        old_n1 = 2**256 - 1
        old_n2 = 2**256 - 1

        debt = 0

        if test_mode:
            resolution = TEST_RESOLUTION
        else:
            resolution = PROD_RESOLUTION
        for block in [
            int(j) for j in numpy.linspace(start_block, end_block - 1, resolution)
        ]:
            t = block
            try:
                h = controller.health(user, False, block_identifier=block) / 1e18
            except ValueError as e:
                times.append(t)
                losses.append(0)
                print(user, t, "nd")
                continue

            new_debt = controller.debt(user, block_identifier=block)
            n1, n2 = amm.read_user_tick_numbers(user, block_identifier=block)

            if (
                debt == 0
                or abs(new_debt - debt) / debt > 0.001
                or n1 != old_n1
                or n2 != old_n2
            ):
                old_health = h
                old_n1 = n1
                old_n2 = n2

            user_row = list(controller.user_state(user, block_identifier=block))
            debt = new_debt
            new_health += old_health - h
            old_health = h

            user_row.append(h)
            user_row.append(new_debt)
            user_row.append(n1)
            user_row.append(n2)

            times.append(t)
            losses.append(new_health * 100)
            [user_data[i].append(user_row[i]) for i in range(custom_data_cols)]

            print(user, t, new_health, h, user_row)

        transposed_user_data = list(zip(*user_data))
        dataframe_data.extend(
            [
                (str(user), t, loss, *user_datum)
                for t, loss, user_datum in zip(times, losses, transposed_user_data)
            ]
        )

        pylab.plot(times, losses, label=str(user))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if test_mode:
        filename = f"scripts/data_test/user_losses_{timestamp}.csv"
    else:
        filename = f"scripts/data/user_losses_{timestamp}.csv"

    df = pd.DataFrame(
        dataframe_data,
        columns=[
            "User",
            "Time",
            "Loss",
            "Collateral",
            "Stablecoin",
            "Debt",
            "N",
            "Health",
            "NewDebt",
            "N1",
            "N2",
        ],
    )
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

    pylab.xlabel("t (blocks)")
    pylab.ylabel("Loss (%)")
    pylab.show()

    elapsed_time = (time.time() - start_time) / 60
    print(f"Runtime: {elapsed_time:.2f} minutes")
