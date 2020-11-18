
def seat_picks_for_pack(pack_size, num_seats, seat_number, picks_per_pack, reverse):
    seat_inc = -1 if reverse else 1

    count = 0
    seat = seat_number
    pickers = []

    while count < pack_size:
        pickers.append(seat)
        if count % picks_per_pack == picks_per_pack - 1:
            seat += seat_inc
        count += 1

    return [x % num_seats for x in pickers]
