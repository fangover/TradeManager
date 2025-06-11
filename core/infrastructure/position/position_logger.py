import csv
import os
from datetime import datetime, timedelta, timezone
from threading import Lock

from models.position import Position


class PositionLogger:
    _lock = Lock()

    def __init__(self, base_dir="out/position"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.current_date = None
        self.file_path = ""
        self.positions = {}
        self.gmt_plus_8 = timezone(timedelta(hours=8))

    def _get_filepath_for_date(self, date: datetime):
        date_str = date.strftime("%y_%m_%d")
        return os.path.join(self.base_dir, f"positions_{date_str}.csv")

    def _init_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "id",
                        "symbol",
                        "direction",
                        "entry_price",
                        "take_profit",
                        "stop_loss",
                        "size",
                        "entry_time",
                        "close_price",
                        "close_time",
                        "pnl",
                        "pnl_pips",
                        "close_reason",
                    ]
                )

    def _load_positions(self):
        self.positions.clear()
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Prevent extra positions data
                    if row["close_time"]:
                        continue
                    self.positions[row["id"]] = row

    def log_position(self, position: Position):
        with self._lock:
            now_gmt8 = datetime.now(self.gmt_plus_8).date()

            if self.current_date != now_gmt8:
                self.current_date = now_gmt8
                self.file_path = self._get_filepath_for_date(
                    datetime.now(self.gmt_plus_8)
                )
                self._init_file()
                self._load_positions()

            entry_time_str = (
                datetime.fromtimestamp(
                    position.entry_time, tz=self.gmt_plus_8  # type: ignore
                ).isoformat()
                if position.entry_time
                else ""
            )

            close_time_str = (
                datetime.fromtimestamp(
                    position.close_time, tz=self.gmt_plus_8  # type: ignore
                ).isoformat()
                if getattr(position, "close_time", None)
                else ""
            )

            new_row = {
                "id": str(position.id),
                "symbol": position.symbol,
                "direction": "BUY" if position.direction == 1 else "SELL",
                "entry_price": position.entry_price,
                "take_profit": (
                    position.take_profit if position.take_profit is not None else ""
                ),
                "stop_loss": (
                    position.stop_loss if position.stop_loss is not None else ""
                ),
                "size": position.size,
                "entry_time": entry_time_str,
                "close_price": (
                    position.close_price if position.close_price is not None else ""
                ),
                "close_time": close_time_str,
                "pnl": getattr(position, "unrealized_pnl", ""),
                "pnl_pips": getattr(position, "unrealized_pnl_pips", ""),
                "close_reason": position.close_reason or "",
            }

            self.positions[str(position.id)] = new_row
            with open(self.file_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=new_row.keys())
                writer.writeheader()
                for row in self.positions.values():
                    writer.writerow(row)

            # Remove closed position to reduce positions data
            keys_to_remove = [
                key for key, row in self.positions.items() if row.get("close_time")
            ]
            for key in keys_to_remove:
                self.positions.pop(key)
