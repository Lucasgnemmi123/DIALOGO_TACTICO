"""Run with Python + playwright installed; uses the installed Chrome browser."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
assert 'color-mix(' not in (ROOT / 'reference-theme.css').read_text(encoding='utf-8'), 'html2canvas no admite color-mix en la TV'

class QuietHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/index.html':
            self.send_response(307)
            self.send_header('Location', '/')
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1366, 'height': 768})
        page = context.new_page()
        errors, external = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: external.append(request.url) if not request.url.startswith(url) else None)
        page.goto(url)
        page.evaluate('navigator.serviceWorker.ready')
        page.wait_for_function('!!navigator.serviceWorker.controller')
        assert page.evaluate("""async () => {
            const cache = await caches.open('dhl-board-shell-v207');
            return (await cache.keys()).length === 28 && !!(await cache.match('./aramark-logo.svg')) && !!(await cache.match('./html2canvas.min.js'));
        }""")
        context.set_offline(True)
        page.reload()
        for width in (1920, 1366, 1080, 1024):
            page.set_viewport_size({'width': width, 'height': 768})
            for summary in (False, True):
                page.evaluate('(value) => document.body.classList.toggle("summary-open", value)', summary)
                assert page.locator('.logo-box img').evaluate_all('(images) => images.length === 2 && images.every(i => i.complete && i.naturalWidth > 0)')
                assert page.locator('.app-header').evaluate('''header => {
                    const items = [...header.children].filter(e => getComputedStyle(e).display !== 'none');
                    return items.every((e, i) => !i || items[i-1].getBoundingClientRect().right <= e.getBoundingClientRect().left + 1);
                }'''), f'Header overlap: {width}, summary={summary}'
        page.evaluate('document.body.classList.remove("summary-open")')
        automatic_week = page.evaluate('isoWeekNumber(new Date())')
        assert page.locator('#weekNumberValue').text_content() == str(automatic_week)
        assert page.locator('#weekNumber').evaluate("element => element.tagName === 'DIV'")
        page.locator('#weekNumber').click()
        assert page.locator('.week-calculator').count() == 0
        assert page.evaluate("isoWeekNumber(new Date(2021, 0, 1)) === 53 && isoWeekNumber(new Date(2021, 0, 4)) === 1")
        page.evaluate("localStorage.setItem('dhl-numero-semana-persistente', JSON.stringify({value:'42'})); paintSystemDate()")
        assert page.locator('#weekNumberValue').text_content() == str(automatic_week)
        assert page.evaluate('typeof html2canvas') == 'function'
        page.evaluate("localStorage.removeItem('dhl-bloc-notas-persistente'); localStorage.removeItem('dhl-notas-teclado-layout')")
        page.reload()
        page.locator('#openNotesCrossDock').click()
        assert page.locator('#notesCrossDockBackdrop').is_visible()
        assert page.locator('#notesPanel').is_visible()
        assert page.locator('.cross-dock-panel').is_visible()
        assert page.locator('#openNotes').count() == 0 and page.locator('#openCrossDock').count() == 0
        split_layout = page.evaluate("""() => {
            const notes = document.querySelector('#notesPanel').getBoundingClientRect();
            const cross = document.querySelector('.cross-dock-panel').getBoundingClientRect();
            const button = document.querySelector('#openNotesCrossDock').getBoundingClientRect();
            return {sideBySide: notes.right <= cross.left, buttonWidth: button.width};
        }""")
        assert split_layout['sideBySide'] and split_layout['buttonWidth'] >= 178
        textarea = page.locator('#importantNotes')
        assert textarea.is_visible()
        assert textarea.get_attribute('readonly') is not None
        assert textarea.get_attribute('inputmode') == 'none'
        assert page.locator('#notesCanvas').count() == 0
        assert page.locator('.drawing-note-pane').count() == 0
        assert page.locator('#notesPanel').evaluate('element => element.getBoundingClientRect().width < 800')
        assert page.locator('#notesKeyboard').is_visible()
        assert page.locator('#notesKeyboard').evaluate("element => element.parentElement === document.body")
        assert page.locator('.notes-keyboard-row').count() == 5
        initial_keyboard_width = page.locator('#notesKeyboard').evaluate('element => element.getBoundingClientRect().width')
        page.locator('[data-note-keyboard-size="larger"]').click()
        assert page.locator('#notesKeyboard').evaluate('(element, width) => element.getBoundingClientRect().width > width', initial_keyboard_width)
        handle = page.locator('[data-note-keyboard-drag]')
        handle_box = handle.bounding_box()
        panel_box = page.locator('#notesPanel').bounding_box()
        keyboard_before = page.locator('#notesKeyboard').bounding_box()
        page.mouse.move(handle_box['x'] + 80, handle_box['y'] + 12)
        page.mouse.down()
        page.mouse.move(88, handle_box['y'] + 42, steps=5)
        page.mouse.up()
        keyboard_after = page.locator('#notesKeyboard').bounding_box()
        assert keyboard_after['x'] != keyboard_before['x'] or keyboard_after['y'] != keyboard_before['y']
        assert keyboard_after['x'] < panel_box['x']
        keyboard_layout = page.evaluate("JSON.parse(localStorage.getItem('dhl-notas-teclado-layout'))")
        assert keyboard_layout['version'] == 2
        assert textarea.evaluate("element => getComputedStyle(element).backgroundPositionY === '11px'")
        page.locator('[data-note-action="accents"]').click()
        assert page.locator('[data-note-key="á"]').count() == 1
        page.locator('[data-note-action="accents"]').click()
        page.locator('[data-note-action="shift"]').click()
        for key in ('h', 'o', 'l', 'a'):
            page.locator(f'[data-note-key="{key}"]').click()
        page.locator('[data-note-action="space"]').click()
        page.locator('[data-note-key="1"]').click()
        assert textarea.input_value() == 'Hola 1'
        stored_notes = page.evaluate("JSON.parse(localStorage.getItem('dhl-bloc-notas-persistente'))")
        assert stored_notes['text'] == 'Hola 1' and 'strokes' not in stored_notes
        page.locator('#closeNotesCrossDock').click()
        persistent_notes = page.evaluate("localStorage.getItem('dhl-bloc-notas-persistente')")
        page.evaluate('resetForNewDay(true)')
        assert page.evaluate("localStorage.getItem('dhl-bloc-notas-persistente')") == persistent_notes
        page.reload()
        assert page.locator('#importantNotes').input_value() == 'Hola 1'
        assert not page.locator('#notesBadge').is_hidden()
        page.evaluate("localStorage.removeItem('dhl-cross-dock-persistente'); readCrossDock(); paintCrossDockButton()")
        assert not page.locator('#openNotesCrossDock').evaluate("element => element.classList.contains('cross-dock-pending') || element.classList.contains('cross-dock-complete')")
        assert page.locator('#crossDockBadge').is_hidden()
        page.locator('#openNotesCrossDock').click()
        page.locator('#addCrossDockRecord').click()
        first_cross = page.locator('.cross-dock-record').first
        first_name = first_cross.locator('[data-cross-name]')
        assert first_name.get_attribute('readonly') is not None
        assert first_name.get_attribute('inputmode') == 'none'
        assert page.locator('body').evaluate("element => element.classList.contains('cross-dock-keyboard-open')")
        assert page.locator('#notesKeyboard').is_visible()
        for key in ('c', 'a', 'r', 'g', 'a'):
            page.locator(f'[data-note-key="{key}"]').click()
        page.locator('[data-note-action="space"]').click()
        for key in ('n', 'o', 'r', 't', 'e'):
            page.locator(f'[data-note-key="{key}"]').click()
        assert first_name.input_value() == 'carga norte'
        first_cross.locator('[data-cross-type-toggle]').click()
        first_cross.locator('[data-cross-type="refri"]').click()
        assert first_cross.locator('.cross-dock-type-menu button.active').count() == 1
        assert first_cross.locator('[data-cross-type="refri"]').get_attribute('aria-pressed') == 'true'
        assert first_cross.locator('[data-cross-type-toggle] small').text_content() == 'REF'
        first_cross.locator('[data-cross-type-toggle]').click()
        first_cross.locator('[data-cross-type="abar"]').click()
        assert first_cross.locator('.cross-dock-type-menu button.active').count() == 1
        assert first_cross.locator('[data-cross-type="abar"]').get_attribute('aria-pressed') == 'true'
        assert first_cross.locator('[data-cross-type-toggle] small').text_content() == 'ABA'
        first_cross.locator('[data-cross-type-toggle]').click()
        first_cross.locator('[data-cross-type="congelado"]').click()
        assert first_cross.locator('.cross-dock-type-menu button.active').count() == 1
        assert first_cross.locator('[data-cross-type="congelado"]').get_attribute('aria-pressed') == 'true'
        assert first_cross.locator('[data-cross-type-toggle] small').text_content() == 'CON'
        assert first_cross.evaluate("element => element.classList.contains('type-congelado')")
        assert first_cross.locator('[data-cross-ready] span').count() == 0
        assert first_cross.locator('[data-cross-ready]').get_attribute('aria-label') == 'Marcar como listo'
        assert page.locator('#openNotesCrossDock').evaluate("element => element.classList.contains('cross-dock-pending')")
        page.locator('.cross-dock-record').first.locator('[data-cross-ready]').click()
        assert page.locator('.cross-dock-record').first.locator('[data-cross-ready]').get_attribute('aria-label') == 'Marcar como pendiente'
        assert page.locator('#openNotesCrossDock').evaluate("element => element.classList.contains('cross-dock-complete')")
        page.locator('#addCrossDockRecord').click()
        second_cross = page.locator('.cross-dock-record').nth(1)
        for key in ('s', 'u', 'r'):
            page.locator(f'[data-note-key="{key}"]').click()
        assert second_cross.locator('[data-cross-name]').input_value() == 'sur'
        second_cross.locator('[data-cross-type-toggle]').click()
        second_cross.locator('[data-cross-type="refri"]').click()
        assert page.locator('#openNotesCrossDock').evaluate("element => element.classList.contains('cross-dock-pending')")
        page.locator('#closeNotesCrossDock').click()
        persistent_cross_dock = page.evaluate("localStorage.getItem('dhl-cross-dock-persistente')")
        page.evaluate('resetForNewDay(true)')
        assert page.evaluate("localStorage.getItem('dhl-cross-dock-persistente')") == persistent_cross_dock
        page.reload()
        assert page.locator('#openNotesCrossDock').evaluate("element => element.classList.contains('cross-dock-pending')")
        page.locator('#openNotesCrossDock').click()
        assert page.locator('.cross-dock-record').count() == 2
        page.locator('#closeNotesCrossDock').click()
        assert page.locator('#notesKeyboard').is_hidden()
        assert page.locator('#captureView span').text_content() == 'Captura BT'
        assert page.locator('#openNotesCrossDock span').text_content() == 'Notas y Cross Docks'
        assert page.locator('.cut-nav > .footer-tools').count() == 1
        assert page.locator('footer > .footer-tools').count() == 0
        screenshot = page.evaluate("""async () => {
            if (document.body.classList.contains('cut-nav-collapsed')) document.querySelector('.cut-nav-toggle').click();
            await minimizeShiftMenuForCapture();
            const capture = await createDashboardScreenshot();
            let shared = false;
            Object.defineProperty(navigator, 'canShare', {configurable: true, value: data => data.files?.[0]?.type === 'image/png'});
            Object.defineProperty(navigator, 'share', {configurable: true, value: async data => { shared = data.files?.[0]?.name.endsWith('.png') }});
            const native = openCapturePreview(capture);
            const beforeDirectClick = shared;
            const help = document.querySelector('#captureHelp').textContent;
            const shareLabel = document.querySelector('#shareCapture span').textContent;
            const shareDisabled = document.querySelector('#shareCapture').disabled;
            await shareScreenshot(capture);
            closeCapturePreview();
            return {type: capture.blob.type, width: capture.width, height: capture.height, native, beforeDirectClick, shared, help, shareLabel, shareDisabled, captureStylesRemoved: !document.querySelector('[data-capture-styles]'), collapsed: document.body.classList.contains('cut-nav-collapsed'), stored: localStorage.getItem('dhl-turnos-colapsados')};
        }""")
        assert screenshot['type'] == 'image/png' and screenshot['width'] == 1024 and screenshot['height'] > 768
        assert screenshot['native'] and not screenshot['beforeDirectClick'] and screenshot['shared'] and not screenshot['shareDisabled']
        assert screenshot['captureStylesRemoved']
        assert screenshot['shareLabel'] == 'Compartir por Bluetooth' and 'no necesita Internet' in screenshot['help']
        assert screenshot['collapsed'] and screenshot['stored'] == 'true'
        page.locator('#openNotesCrossDock').click()
        page.locator('#clearNotes').click()
        cleared_notes = page.evaluate("JSON.parse(localStorage.getItem('dhl-bloc-notas-persistente'))")
        assert cleared_notes['text'] == '' and 'strokes' not in cleared_notes
        page.locator('#closeNotesCrossDock').click()
        kilos_layout = page.evaluate("""() => {
            const board = document.querySelector('.board').getBoundingClientRect();
            const operations = document.querySelector('.operations').getBoundingClientRect();
            const side = document.querySelector('.side-panel').getBoundingClientRect();
            const footer = document.querySelector('footer').getBoundingClientRect();
            return {
                attached: Math.abs(board.bottom - footer.top) <= 1 && Math.abs(operations.bottom - footer.top) <= 1 && Math.abs(side.bottom - footer.top) <= 1,
                visible: Math.abs(footer.bottom - innerHeight) <= 1 && Math.round(footer.height) === 42,
                title: parseFloat(getComputedStyle(document.querySelector('#expectedKilosLabel')).fontSize) >= 10,
                roles: parseFloat(getComputedStyle(document.querySelector('.expected-kilos label b')).fontSize) >= 11,
                values: parseFloat(getComputedStyle(document.querySelector('#expectedKilosIn')).fontSize) >= 22
            };
        }""")
        assert all(kilos_layout.values()), kilos_layout
        gaussian = page.evaluate("""() => {
            const cuts = ['01:00','03:00','05:00','09:00','11:00','13:00','17:00','19:00','21:00'];
            const records = cuts.map(cut => ({cut}));
            const shift = index => index < 3 ? 'noche' : index < 6 ? 'manana' : 'tarde';
            const parse = html => new DOMParser().parseFromString(html, 'text/html');
            const a = parse(productivityDistributionHtml(records, [-18,-13,-8,-2,0,4,9,14,19], shift));
            const b = parse(productivityDistributionHtml(records, [-6,-4,-2,0,2,4,6,8,10], shift));
            const curve = a.querySelector('.gaussian-line').getAttribute('d');
            const points = [...curve.matchAll(/[ML]([\\d.]+),([\\d.]+)/g)].map(match => ({x: Number(match[1]), y: Number(match[2])}));
            const peak = points.reduce((best, point) => point.y < best.y ? point : best, points[0]);
            const labels = [...a.querySelectorAll('.distribution-point-label')].map(label => label.textContent);
            return {
                fixed: curve === b.querySelector('.gaussian-line').getAttribute('d'),
                centered: Math.abs(peak.x - 322) < .2,
                noMovingMean: !a.querySelector('.distribution-mean'),
                labeled: cuts.every(cut => labels.some(label => label.includes(cut)))
            };
        }""")
        assert gaussian == {'fixed': True, 'centered': True, 'noMovingMean': True, 'labeled': True}
        for selector, digits in (('#expectedKilosIn', '1234567890'), ('#expectedKilosOut', '9876543')):
            field = page.locator(selector)
            assert field.get_attribute('readonly') == ''
            assert field.get_attribute('inputmode') == 'none'
            field.click()
            assert page.locator('.kilos-calculator').is_visible()
            for digit in digits:
                page.locator(f'.kilos-calculator [data-key="{digit}"]').click()
            page.locator('.kilos-calculator .calculator-save').click()
        assert page.locator('#expectedKilosIn').input_value() == '123.456.789'
        assert page.locator('#expectedKilosOut').input_value() == '9.876.543'
        draft = page.evaluate('JSON.parse(localStorage.getItem("dhl-reuniones-diarias-json"))')
        assert draft['expectedKilos'] == {'in': '123456789', 'out': '9876543'}
        assert draft['drafts']['01:00']['expectedKilos'] == {'in': '123456789', 'out': '9876543'}
        page.locator('#saveMeeting').click()
        meeting = page.evaluate('JSON.parse(localStorage.getItem("dhl-reuniones-diarias-json"))')
        assert meeting['sessions']['01:00']['expectedKilos'] == {'in': '123456789', 'out': '9876543'}
        page.reload()
        assert page.locator('#expectedKilosIn').input_value() == '123.456.789'
        assert page.locator('#expectedKilosOut').input_value() == '9.876.543'
        page.evaluate('resetForNewDay(true)')
        assert page.locator('#expectedKilosIn').input_value() == ''
        assert page.locator('#expectedKilosOut').input_value() == ''
        cleared = page.evaluate('JSON.parse(localStorage.getItem("dhl-reuniones-diarias-json")).expectedKilos')
        assert cleared == {'in': '', 'out': ''}
        page.evaluate('simulateMeetingData()')
        assert page.locator('#expectedKilosIn').input_value()
        assert page.locator('#expectedKilosOut').input_value()
        page.locator('#saveMeeting').click()
        saved = page.evaluate('localStorage.getItem("dhl-reuniones-diarias-json")')
        assert saved
        page.reload()
        assert page.evaluate('localStorage.getItem("dhl-reuniones-diarias-json")') == saved
        page.locator('#focusMode').click()
        assert page.locator('body').evaluate("element => element.classList.contains('summary-open') && element.classList.contains('focus-summary-open')")
        assert page.locator('.column-head.blank > #focusMode').count() == 1
        assert page.locator('.focus-chart-card').count() == 3
        assert page.locator('.focus-progress-point').count() > 0
        assert page.locator('.focus-progress-now strong').count() == 3
        assert page.locator('#toggleFocusDemo').count() == 0
        assert page.locator('.focus-chart-card.preparacion .focus-workload-bar').count() == 1
        assert page.locator('.focus-chart-card.preparacion .focus-progress-now small').text_content() == 'Preparado / carga total'
        assert page.locator('#closeSummary').text_content().strip() == 'Datos'
        page.locator('#closeSummary').click()
        assert not page.locator('body').evaluate("element => element.classList.contains('summary-open')")
        assert page.locator('#focusMode span').text_content() == 'Foco'
        assert page.locator('#carouselMode span').text_content() == 'Carrusel'
        page.evaluate("""() => {
            window.__carouselNativeSetInterval = window.setInterval;
            window.__carouselNativeClearInterval = window.clearInterval;
            window.__carouselTick = null;
            window.setInterval = (callback, delay) => delay === 8000
                ? (window.__carouselTick = callback, 987654321)
                : window.__carouselNativeSetInterval(callback, delay);
            window.clearInterval = id => id === 987654321
                ? (window.__carouselTick = null)
                : window.__carouselNativeClearInterval(id);
        }""")
        page.locator('#carouselMode').click()
        assert page.locator('#carouselMode span').text_content() == 'Detener'
        page.evaluate('window.__carouselTick()')
        assert page.locator('body').evaluate("element => element.classList.contains('focus-summary-open')")
        page.evaluate('window.__carouselTick()')
        assert page.locator('[data-summary-area="recepcion"]').evaluate("element => element.classList.contains('active')")
        page.evaluate('window.__carouselTick()')
        assert page.locator('[data-summary-area="preparacion"]').evaluate("element => element.classList.contains('active')")
        page.evaluate('window.__carouselTick()')
        assert page.locator('[data-summary-area="despacho"]').evaluate("element => element.classList.contains('active')")
        page.evaluate('window.__carouselTick()')
        assert not page.locator('body').evaluate("element => element.classList.contains('summary-open')")
        page.locator('#carouselMode').click()
        assert page.locator('#carouselMode span').text_content() == 'Carrusel'
        page.evaluate("""() => {
            window.setInterval = window.__carouselNativeSetInterval;
            window.clearInterval = window.__carouselNativeClearInterval;
            delete window.__carouselNativeSetInterval;
            delete window.__carouselNativeClearInterval;
            delete window.__carouselTick;
        }""")
        page.goto(url + '?offline-check=1#resumen')
        assert page.locator('body').evaluate('e => e.classList.contains("summary-open")')
        assert page.locator('.logo-box .aramark-logo').evaluate('i => i.complete && i.naturalWidth > 0')
        assert not errors, errors
        assert not external, external
        browser.close()
        print('PASS: cached shell, shared movable keyboard, persistent Cross Dock, Foco charts from saved meetings, offline capture/share, kilos layout and responsive header; no external requests or JS errors.')
finally:
    server.shutdown()
