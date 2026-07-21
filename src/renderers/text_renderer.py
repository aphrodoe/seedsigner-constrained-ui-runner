"""
TextRenderer: Core text layout engine for character LCD displays.
"""

from typing import List
from src.screen_state import ScreenState, ScreenType
from src.renderers.text_helpers import TextHelpersMixin
from src.renderers.screens.button_list import ButtonListMixin
from src.renderers.screens.main_menu import MainMenuMixin
from src.renderers.screens.status import StatusMixin
from src.renderers.screens.keyboard import KeyboardMixin
from src.renderers.screens.mnemonic_entry import MnemonicEntryMixin
from src.renderers.screens.psbt import PSBTMixin
from src.renderers.screens.seed_screens import SeedScreensMixin
from src.renderers.screens.address_screens import AddressScreensMixin
from src.renderers.screens.tools_screens import ToolsScreensMixin
from src.renderers.screens.simple_screens import SimpleScreensMixin

class TextRenderer(
    TextHelpersMixin,
    ButtonListMixin,
    MainMenuMixin,
    StatusMixin,
    KeyboardMixin,
    MnemonicEntryMixin,
    PSBTMixin,
    SeedScreensMixin,
    AddressScreensMixin,
    ToolsScreensMixin,
    SimpleScreensMixin,
):
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        # Number of rows available for items (row 0 is always the title)
        self.item_rows = rows - 1
        self.tier = self._determine_tier()

    def render(self, state: ScreenState) -> List[str]:
        """Return exactly `self.rows` strings, each exactly `self.cols` chars wide."""
        # Visual-only screens (camera, QR, I/O test) — not applicable to text UI
        if state.screen_type.is_visual_only():
            title = state.context.get("top_nav", {}).get("title", "Visual Only")
            lines = [self._title_row(title, "", state)]
            lines.append(self._center("[Visual Only]"))
            lines.append(self._center("No text-UI"))
            return self._pad_rows(lines)

        if state.screen_type == ScreenType.BUTTON_LIST:
            lines = self._render_button_list(state)
        elif state.screen_type == ScreenType.MAIN_MENU:
            lines = self._render_main_menu(state)
        elif state.screen_type == ScreenType.LARGE_ICON_STATUS:
            lines = self._render_status(state)
        elif state.screen_type == ScreenType.SEED_MNEMONIC_ENTRY:
            lines = self._render_seed_mnemonic_entry(state)
        elif state.screen_type.is_keyboard():
            lines = self._render_keyboard(state)
        elif state.screen_type == ScreenType.SPLASH:
            lines = self._render_splash(state)
        elif state.screen_type == ScreenType.PSBT_OVERVIEW:
            lines = self._render_psbt_overview(state)
        elif state.screen_type == ScreenType.PSBT_ADDRESS_DETAILS:
            lines = self._render_psbt_address_details(state)
        elif state.screen_type == ScreenType.PSBT_CHANGE_DETAILS:
            lines = self._render_psbt_change_details(state)
        elif state.screen_type == ScreenType.PSBT_MATH:
            lines = self._render_psbt_math(state)
        elif state.screen_type == ScreenType.LOCALE_PICKER:
            lines = self._render_locale_picker(state)
        elif state.screen_type == ScreenType.SEED_FINALIZE:
            lines = self._render_seed_finalize(state)
        elif state.screen_type == ScreenType.LOADING:
            lines = self._render_loading(state)
        elif state.screen_type == ScreenType.SCREENSAVER:
            lines = []
            padding_top = max(0, (self.rows - 1) // 2)
            for _ in range(padding_top):
                lines.append(self._center(""))
            lines.append(self._center("SeedSigner"))
            lines = self._pad_rows(lines[:self.rows])
        # ── New screen renderers ────────────────────────────────────
        elif state.screen_type == ScreenType.TOAST_OVERLAY:
            lines = self._render_toast_overlay(state)
        elif state.screen_type == ScreenType.SEED_EXPORT_XPUB_DETAILS:
            lines = self._render_seed_export_xpub_details(state)
        elif state.screen_type == ScreenType.SEED_REVIEW_PASSPHRASE:
            lines = self._render_seed_review_passphrase(state)
        elif state.screen_type == ScreenType.SEED_WORDS:
            lines = self._render_seed_words(state)
        elif state.screen_type == ScreenType.MULTISIG_WALLET_DESCRIPTOR:
            lines = self._render_multisig_wallet_descriptor(state)
        elif state.screen_type == ScreenType.SEED_TRANSCRIBE_SEEDQR_FORMAT:
            lines = self._render_seed_transcribe_seedqr_format(state)
        elif state.screen_type == ScreenType.SEED_SIGN_MESSAGE_CONFIRM_ADDRESS:
            lines = self._render_seed_sign_message_confirm_address(state)
        elif state.screen_type == ScreenType.SEED_SIGN_MESSAGE_CONFIRM_MESSAGE:
            lines = self._render_seed_sign_message_confirm_message(state)
        elif state.screen_type == ScreenType.SEED_ADDRESS_VERIFICATION:
            lines = self._render_seed_address_verification(state)
        elif state.screen_type == ScreenType.SEED_ADDRESS_VERIFICATION_SUCCESS:
            lines = self._render_seed_address_verification_success(state)
        elif state.screen_type == ScreenType.TOOLS_CALC_FINAL_WORD:
            lines = self._render_tools_calc_final_word(state)
        elif state.screen_type == ScreenType.TOOLS_CALC_FINAL_WORD_DONE:
            lines = self._render_tools_calc_final_word_done(state)
        elif state.screen_type == ScreenType.TOOLS_ADDRESS_EXPLORER_ADDRESS_LIST:
            lines = self._render_tools_address_explorer_list(state)
        elif state.screen_type == ScreenType.TOOLS_ADDRESS_EXPLORER_ADDRESS_TYPE:
            lines = self._render_tools_address_explorer_type(state)
        elif state.screen_type == ScreenType.SETTINGS_QR_CONFIRMATION:
            lines = self._render_settings_qr_confirmation(state)
        elif state.screen_type in (ScreenType.DONATE, ScreenType.RESET,
                                    ScreenType.POWER_OFF_NOT_REQUIRED):
            lines = self._render_text_only(state)
        # ── Button-list fallback screens ────────────────────────────
        elif state.screen_type == ScreenType.POWER_OPTIONS:
            lines = self._render_button_list(state)
        elif state.screen_type == ScreenType.PSBT_OP_RETURN:
            lines = self._render_psbt_op_return(state)
        else:
            lines = self._pad_rows([self._center("Unsupported")])
            
        toast_msg = state.context.get("toast")
        if toast_msg:
            toast_msg = toast_msg.replace("\n", " ").strip()
            max_label = self.cols - 4
            if len(toast_msg) > max_label:
                diff = len(toast_msg) - max_label
                total_frames = diff + 10
                frame = state.marquee_tick % total_frames
                if frame < 5: offset = 0
                elif frame >= 5 + diff: offset = diff
                else: offset = frame - 5
                visible = toast_msg[offset : offset + max_label]
                toast_text = f"[ {visible} ]"
            else:
                toast_text = f"[ {toast_msg} ]"
            lines[-1] = self._center(toast_text)
            
        return lines

    # ── button_list_screen ──────────────────────────────────────────

