import sys
import os
import shutil

import webview
import json
from pathlib import Path
import logging
import subprocess
import logging.handlers
from app import app, tasks_db, app_data_dir

# --- FFmpeg/FFprobe パス解決 ---
def get_ffmpeg_path():
    """
    FFmpeg/FFprobeのバイナリへの絶対パスを取得します。
    開発環境 (.py) とパッケージ化された環境 (PyInstaller) の両方で動作します。
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller実行時: sys._MEIPASS/bin/ffmpeg.exe
        base_path = Path(sys._MEIPASS)
        ffmpeg_path = base_path / 'bin' / 'ffmpeg.exe'
        ffprobe_path = base_path / 'bin' / 'ffprobe.exe'
    else:
        # 開発時: desktop_app/bin/ffmpeg.exe（setup_ffmpeg.py の配置先）
        base_path = Path(__file__).resolve().parent
        ffmpeg_path = base_path / 'bin' / 'ffmpeg.exe'
        ffprobe_path = base_path / 'bin' / 'ffprobe.exe'

    if not ffmpeg_path.exists() or not ffprobe_path.exists():
        error_msg = f"FFmpeg or FFprobe not found. Searched in: {ffmpeg_path.parent}"
        raise FileNotFoundError(error_msg)

    return str(ffmpeg_path), str(ffprobe_path)

# --- アプリケーションデータディレクトリの設定 ---
# 設定・ログは app.py の一時ファイルと同じ LocalAppData 配下に保存します。
# 例: C:\Users\<ユーザー名>\AppData\Local\MP4-to-GIF-Converter
# 旧版はホーム直下の ~/.mp4togifconverter を使っていたため、初回起動時に移します。
LEGACY_APP_DATA_DIR = Path.home() / ".mp4togifconverter"

def _migrate_legacy_app_data(old_dir: Path, new_dir: Path) -> None:
    """旧ホーム配下の設定・ログを LocalAppData へ、未コピー分だけ移す。"""
    try:
        if not old_dir.is_dir():
            return
        if old_dir.resolve() == new_dir.resolve():
            return
        for src in old_dir.iterdir():
            if not src.is_file():
                continue
            dst = new_dir / src.name
            if dst.exists():
                continue
            shutil.copy2(src, dst)
    except Exception as e:
        print(f"WARNING: Could not migrate legacy app data from {old_dir}: {e}", file=sys.stderr)

try:
    APP_DATA_DIR = Path(app_data_dir)
    APP_DATA_DIR.mkdir(exist_ok=True)
    _migrate_legacy_app_data(LEGACY_APP_DATA_DIR, APP_DATA_DIR)
except Exception as e:
    # データディレクトリが作れない稀なケースではカレントディレクトリにフォールバック
    # この時点ではロガーが未設定のため、標準エラー出力にフォールバック
    print(f"CRITICAL: Could not create app data directory, falling back to current dir: {e}", file=sys.stderr)
    APP_DATA_DIR = Path('.')

# --- ロギング設定 ---
LOG_FILE = APP_DATA_DIR / 'app.log'

def setup_logging(is_debug=False):
    """アプリケーションのロギングを設定する"""
    log_level = logging.DEBUG if is_debug else logging.INFO

    # ルートロガーを取得し、レベルを設定
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 既存のハンドラをクリア（重複を避けるため）
    if logger.hasHandlers():
        logger.handlers.clear()

    # ログのフォーマットを定義
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # ファイルハンドラの設定 (ログローテーション付き)
    # 1MBごとにファイルを分け、5世代までバックアップを保持
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"CRITICAL: Could not create log file handler: {e}", file=sys.stderr)

    logging.info("--- Application Starting ---")

def load_config():
    """設定ファイルを読み込む"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(config):
    """設定ファイルを保存する"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving config: {e}", exc_info=True)

# --- ファイルパスの定義 ---
# 設定ファイルとタスクDBのパスをアプリケーションデータディレクトリ内に設定
CONFIG_FILE = APP_DATA_DIR / 'pywebview_config.json'
DB_FILE = APP_DATA_DIR / 'tasks_db.json'

DEFAULT_FORM_WIDTH = 640
DEFAULT_WINDOW_HEIGHT = 960
# プレビュー枠（常時表示）用の幅
PREVIEW_EXTRA_WIDTH = 640
DEFAULT_WINDOW_WIDTH = DEFAULT_FORM_WIDTH + PREVIEW_EXTRA_WIDTH

def migrate_layout_with_preview(config):
    """
    旧版はフォーム幅のみを保存していたため、常時プレビューレイアウトへ移行する。
    一度だけ幅に PREVIEW_EXTRA_WIDTH を加算する。
    """
    if config.get('layout_with_preview'):
        return config
    try:
        width = int(config.get('window_width', DEFAULT_FORM_WIDTH))
    except (TypeError, ValueError):
        width = DEFAULT_FORM_WIDTH
    # フォーム幅相当ならプレビュー分を足す（既に広い場合はそのまま）
    if width < DEFAULT_WINDOW_WIDTH:
        config['window_width'] = width + PREVIEW_EXTRA_WIDTH
    else:
        config['window_width'] = width
    config['layout_with_preview'] = True
    save_config(config)
    logging.info(
        f"Migrated window width for always-on preview: {width} -> {config['window_width']}"
    )
    return config

def get_window_geometry(config):
    """設定からウィンドウのサイズ・位置を取得する。未設定時はデフォルト。"""
    try:
        width = int(config.get('window_width', DEFAULT_WINDOW_WIDTH))
        height = int(config.get('window_height', DEFAULT_WINDOW_HEIGHT))
    except (TypeError, ValueError):
        width, height = DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT

    width = max(DEFAULT_WINDOW_WIDTH // 2, width)
    height = max(100, height)

    geometry = {'width': width, 'height': height}

    x = config.get('window_x')
    y = config.get('window_y')
    try:
        if x is not None and y is not None:
            geometry['x'] = int(x)
            geometry['y'] = int(y)
    except (TypeError, ValueError):
        pass

    return geometry

def save_window_geometry(window, config):
    """現在のウィンドウサイズ・位置を設定に保存する。"""
    try:
        config['window_width'] = int(window.width)
        config['window_height'] = int(window.height)
        config['window_x'] = int(window.x)
        config['window_y'] = int(window.y)
        config['layout_with_preview'] = True
        save_config(config)
        logging.info(
            "Saved window geometry: "
            f"{config['window_width']}x{config['window_height']} "
            f"@ ({config['window_x']}, {config['window_y']})"
        )
    except Exception as e:
        logging.error(f"Failed to save window geometry: {e}", exc_info=True)

def save_tasks_on_close():
    """ウィンドウが閉じられた後にタスクDBをJSONファイルに保存します。"""
    logging.info("Application closed. Saving task history.")
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks_db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Failed to save task history on close: {e}", exc_info=True)

def load_tasks_on_startup():
    """起動時にJSONファイルからタスクDBを読み込みます。"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            tasks_db.update(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # ファイルが存在しない、または空の場合は何もしない

class Api:
    """ pywebviewのJS APIとしてフロントエンドに公開するクラス """
    def __init__(self):
        self.config = migrate_layout_with_preview(load_config())

    def select_file(self):
        """
        ファイル選択ダイアログを開き、選択されたファイルのパスを返す。
        """
        window = webview.active_window()
        if not window:
            return None
        
        initial_dir = self.config.get('last_input_dir') or ''

        file_types = ('MP4 Files (*.mp4)',)
        result = window.create_file_dialog(
            webview.FileDialog.OPEN, directory=initial_dir, file_types=file_types
        )
        
        if result:
            selected_path = result[0]
            self.config['last_input_dir'] = os.path.dirname(selected_path)
            save_config(self.config)
            return selected_path
        return None

    def select_folder(self):
        """
        フォルダ選択ダイアログを開き、選択されたフォルダのパスを返す。
        """
        window = webview.active_window()
        if not window:
            return None
            
        initial_dir = self.config.get('last_output_dir') or ''

        result = window.create_file_dialog(webview.FileDialog.FOLDER, directory=initial_dir)

        if result:
            selected_path = result[0]
            self.config['last_output_dir'] = selected_path
            save_config(self.config)
            return selected_path
        return None

    def get_last_output_dir(self):
        """最後に使用した保存先フォルダのパスを返す"""
        return self.config.get('last_output_dir', '')

    def get_conversion_settings(self):
        """最後に使用した変換設定（FPS / 幅 / 高品質 / プレビュー再生モード）を返す"""
        mode = self.config.get('preview_playback_mode', 'once')
        if mode not in ('loop', 'once'):
            mode = 'once'
        return {
            'fps': self.config.get('fps', 15),
            'width': self.config.get('width', 640),
            'high_quality': bool(self.config.get('high_quality', False)),
            'preview_playback_mode': mode,
        }

    def save_conversion_settings(self, fps, width, high_quality):
        """変換設定を永続化する"""
        try:
            self.config['fps'] = int(fps)
            self.config['width'] = int(width)
            self.config['high_quality'] = bool(high_quality)
            save_config(self.config)
            return True
        except (TypeError, ValueError) as e:
            logging.error(f"Invalid conversion settings: {e}", exc_info=True)
            return False

    def save_preview_playback_mode(self, mode):
        """プレビューの再生モード（loop / once）を永続化する"""
        if mode not in ('loop', 'once'):
            mode = 'once'
        self.config['preview_playback_mode'] = mode
        save_config(self.config)
        return True

    def open_log_folder(self):
        """
        ログファイルが保存されているフォルダをOSのファイルエクスプローラーで開く。
        """
        try:
            folder_path = str(APP_DATA_DIR.resolve())
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', folder_path])
            else: # Linux
                subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            logging.error(f"Failed to open log folder '{APP_DATA_DIR}': {e}", exc_info=True)
            # フロントエンドにはエラーを返さない。ログに記録されていれば十分。

def make_on_closing(api):
    """
    ウィンドウが閉じられる前のハンドラを生成する。
    終了確認のあと、ウィンドウサイズ・位置を保存する。
    """
    def on_closing():
        is_task_running = any(
            task.get('state') not in ('SUCCESS', 'FAILURE')
            for task in tasks_db.values()
        )

        window = webview.active_window()

        if is_task_running:
            if window:
                confirm_close = window.create_confirmation_dialog(
                    '終了の確認',
                    '変換中のタスクがあります。本当にアプリケーションを終了しますか？'
                )
                if not confirm_close:
                    return False

        if window:
            save_window_geometry(window, api.config)

        return True

    return on_closing

def get_icon_path():
    """
    アプリアイコン (app_icon.ico) へのパスを返す。
    開発時はプロジェクトルート、PyInstaller 実行時は _MEIPASS / exe 隣を探す。
    """
    candidates = []
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.append(Path(sys._MEIPASS) / 'app_icon.ico')
        candidates.append(Path(sys.executable).resolve().parent / 'app_icon.ico')
    else:
        candidates.append(Path(__file__).resolve().parent.parent / 'app_icon.ico')

    for path in candidates:
        if path.is_file():
            return str(path)
    return None

def main():
    # コマンドライン引数に '--debug' が含まれていればデバッグモードを有効にする
    is_debug = '--debug' in sys.argv

    # アプリケーションのロギングを設定
    setup_logging(is_debug)

    icon_path = get_icon_path()
    if icon_path:
        logging.info(f"App icon found at: {icon_path}")
    else:
        logging.warning("App icon (app_icon.ico) not found")

    # --- FFmpegのパスを設定 ---
    try:
        ffmpeg_path, ffprobe_path = get_ffmpeg_path()
        app.config['FFMPEG_PATH'] = ffmpeg_path
        app.config['FFPROBE_PATH'] = ffprobe_path
        logging.info(f"FFmpeg found at: {ffmpeg_path}")
    except FileNotFoundError as e:
        logging.critical(e)
        # FFmpegが見つからない場合、GUIでエラーを表示して終了
        webview.create_window(
            '致命的なエラー',
            html=f'<h1>FFmpegが見つかりません</h1><p>アプリケーションの動作に必要なFFmpegが見つかりませんでした。</p><p>エラー詳細: {e}</p><p>アプリケーションを終了します。</p>',
            width=600,
            height=250
        )
        err_start = {}
        if icon_path:
            err_start['icon'] = icon_path
        webview.start(**err_start)
        sys.exit(1) # 終了

    # デスクトップアプリとして実行されていることをFlaskアプリに伝える
    app.config['IS_DESKTOP_APP'] = True
    api = Api()

    # 起動時に以前のタスク履歴を読み込む
    load_tasks_on_startup()

    # 前回のウィンドウサイズ・位置を復元（なければデフォルト）
    geometry = get_window_geometry(api.config)
    logging.info(f"Restoring window geometry: {geometry}")

    window = webview.create_window(
        'MP4 to GIF Converter 2',
        app,
        js_api=api,
        resizable=True,
        **geometry,
    )

    # ウィンドウが閉じられる際のイベントにハンドラを接続
    window.events.closing += make_on_closing(api)
    # ウィンドウが完全に閉じられた後のイベントにハンドラを接続
    window.events.closed += save_tasks_on_close

    # http_server=True は create_window ではなく start に渡します
    # icon は Windows でも .ico を指定可能（pywebview 6.2+）
    start_kwargs = {'debug': is_debug, 'http_server': True}
    if icon_path:
        start_kwargs['icon'] = icon_path
    webview.start(**start_kwargs)
 
if __name__ == '__main__':
    main()
