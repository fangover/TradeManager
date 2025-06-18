import threading
import tkinter as tk
from tkinter import ttk

from core.application.state import TradingState
from models import Position


class PositionMonitor(tk.Tk):
    def __init__(self, state: TradingState, refresh_ms: int = 1000) -> None:
        super().__init__()
        self.state = state
        self.refresh_ms = refresh_ms
        self.title("TradeManager - Open Positions")
        self.geometry("800x200")

        columns = (
            "id",
            "type",
            "open",
            "current",
            "size",
            "pnl",
            "pips",
            "reason",
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=90, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.stop_event = threading.Event()
        self.after(0, self.refresh)

    def refresh(self) -> None:
        if self.stop_event.is_set():
            self.destroy()
            return
        self.tree.delete(*self.tree.get_children())
        for pos in list(self.state.position_manager.open_positions.values()):
            pos = pos  # type: Position
            self.tree.insert(
                "",
                tk.END,
                values=(
                    pos.id,
                    "BUY" if pos.direction == 1 else "SELL",
                    f"{pos.entry_price:.2f}",
                    f"{pos.current_price:.2f}",
                    f"{pos.size:.2f}",
                    f"{pos.unrealized_pnl:.2f}",
                    f"{pos.unrealized_pnl_pips:.1f}",
                    pos.comment,
                ),
            )
        self.after(self.refresh_ms, self.refresh)

    def on_close(self) -> None:
        self.stop_event.set()
        self.destroy()

    def close(self) -> None:
        self.stop_event.set()


def start_position_monitor(
    state: TradingState,
) -> tuple[PositionMonitor, threading.Thread]:

    ready = threading.Event()
    container: dict[str, PositionMonitor] = {}

    def thread_target():
        monitor = PositionMonitor(state)
        container["monitor"] = monitor
        ready.set()
        monitor.mainloop()

    thread = threading.Thread(target=thread_target, daemon=True)
    thread.start()
    ready.wait()
    return container["monitor"], thread
