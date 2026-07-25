import { useContext, useEffect, useRef } from 'react';
import SettingsContext from '@shikkhahub/shared/src/contexts/SettingsContext';
import { useContentScriptStatus } from '@shikkhahub/shared/src/hooks';
import { useExtensionContext } from '@shikkhahub/shared/src/contexts/ExtensionContext';

export const useCompanionSettings = (): void => {
  const isOnLoad = useRef(true);
  const { optOutCompanion, loadedSettings } = useContext(SettingsContext);
  const { registerBrowserContentScripts } = useExtensionContext();
  const { contentScriptGranted } = useContentScriptStatus();

  useEffect(() => {
    if (optOutCompanion || contentScriptGranted || !loadedSettings) {
      return;
    }

    if (isOnLoad.current) {
      isOnLoad.current = false;
      return;
    }

    // Edge case for Brave browser where this only exists if accepted
    registerBrowserContentScripts?.();
    // @NOTE see https://shikkhahub.atlassian.net/l/cp/dK9h1zoM
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [optOutCompanion, loadedSettings]);
};
