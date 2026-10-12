#!/usr/bin/env python3
import random
import subprocess
import time
from datetime import datetime

import requests
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
SERVICE_URL = "http://127.0.0.1:8080/health"
COMPOSE = ["docker", "compose"]

CAT_MESSAGES = {
    "healthy": [
        "Мурчик мурчит. Прод живёт свою лучшую жизнь.",
        "Мурик уснул на клавиатуре. Пока всё стабильно.",
        "Никаких инцидентов. Кот подозрительно доволен."
    ],
    "incident": [
        "МЯУ?! Кто выключил мой сервер?!",
        "Мурчик уронил прод.... Он утверждает, что это был эксперимент.",
        "Мурик смотрит на красный алерт с видом невиновного."
    ],
    "recovered": [
        "Сервис снова жив! Мурчик требует вкусняшку за работу SRE.",
        "Инцидент устранён. Мурчага записал это себе в достижения.",
        "Восстановление завершено. Мурчик: «Я так и планировал»."
    ],
}

def run(*args, check=True, capture=False):
    return subprocess.run(
        [*COMPOSE, *args], check=check, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )

def is_healthy():
    try:
        return requests.get(SERVICE_URL, timeout=1.5).status_code == 200
    except requests.RequestException:
        return False

def ensure_docker():
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=5)
    except Exception:
        console.print("[red]Docker недоступен. Запусти Docker Desktop/daemon и повтори.[/red]")
        raise SystemExit(1)

def wait_for_health(seconds=25):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_healthy():
            return True
        time.sleep(1)
    return False

def header(xp, level):
    console.print(Panel.fit(
        "[bold orange1]MURCHIKOPS[/bold orange1]  [white]Мяу! Я Мурчик, работа кипит - прямо под лапами.[/white]\n"
        "[dim]Tamagotchi × Chaos Engineering[/dim]",
        border_style="bright_green"
    ))
    console.print(f"Мурчик: [bold yellow]Level {level}[/bold yellow]  XP: [bold cyan]{xp}[/bold cyan]")

def main():
    ensure_docker()
    xp, incidents, level = 0, 0, 1
    console.print("[cyan]Поднимаю изолированный тестовый сервис...[/cyan]")
    run("up", "-d", "--build")
    if not wait_for_health():
        console.print("[red]Сервис не выздоровел. Проверь `docker compose logs app`.[/red]")
        raise SystemExit(1)

    while True:
        header(xp, level)
        status = "[green]ONLINE[/green]" if is_healthy() else "[red]OFFLINE[/red]"
        console.print(f"Сервис: {status}")
        console.print("\n[bold]Меню[/bold]")
        console.print(" [green]1[/green] — проверить здоровье")
        console.print(" [red]2[/red] — позволить Мурчику устроить аварию")
        console.print(" [cyan]3[/cyan] — посмотреть журнал инцидентов")
        console.print(" [yellow]4[/yellow] — выйти и остановить")
        choice = console.input("\n[bold]> [/bold]").strip()

        if choice == "1":
            if is_healthy():
                console.print("[green]✓ /health вернул 200 OK[/green]")
                console.print(random.choice(CAT_MESSAGES["healthy"]))
            else:
                console.print("[red]✗ Health check провален[/red]")
            console.input("\nEnter для продолжения...")
        elif choice == "2":
            incidents += 1
            started = time.monotonic()
            console.print(Panel(random.choice(CAT_MESSAGES["incident"]), border_style="red"))
            run("stop", "app")
            console.print("[yellow]Алерт: приложение недоступно. Восстанавливаю сервис...[/yellow]")
            time.sleep(2)
            run("up", "-d", "app")
            if wait_for_health():
                elapsed = time.monotonic() - started
                xp += 25
                level = 1 + xp // 50
                console.print(Panel(
                    f"[green]Сервис восстановлен за {elapsed:.1f} сек.[/green]\n"
                    f"{random.choice(CAT_MESSAGES['recovered'])}\n"
                    f"[bold cyan]+25 XP[/bold cyan] · Инцидентов пережито: {incidents}",
                    title="Recovery report", border_style="green"
                ))
                if incidents == 1:
                    console.print("[bold yellow]Достижение открыто: «Первый инцидент»[/bold yellow]")
                if incidents == 3:
                    console.print("[bold yellow]Достижение открыто: «Мурчик не сломает нас»[/bold yellow]")
            else:
                console.print("[red]Автовосстановление не удалось. Посмотри `docker compose logs app`.[/red]")
            console.input("\nEnter для продолжения...")
        elif choice == "3":
            table = Table(title="CatOps Incident Journal", box=box.ROUNDED)
            table.add_column("Время", style="cyan")
            table.add_column("Событие")
            table.add_column("Результат")
            table.add_row(datetime.now().strftime("%H:%M:%S"), "Стенд запущен", "HEALTHY")
            if incidents:
                table.add_row(datetime.now().strftime("%H:%M:%S"), f"Симулировано аварий: {incidents}", "Восстановление проверено")
            console.print(table)
            console.input("\nEnter для продолжения...")
        elif choice == "4":
            run("down", check=False)
            console.print("[cyan]Стенд остановлен. Мурчик ушёл спать. Пока-пока, мяу![/cyan]")
            break
        else:
            console.print("[yellow]Выбери 1, 2, 3 или 4.[/yellow]")

if __name__ == "__main__":
    main()
