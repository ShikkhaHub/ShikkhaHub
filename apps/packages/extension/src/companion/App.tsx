import type { ReactElement } from 'react';
import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import browser from 'webextension-polyfill';
import type { Boot } from '@shikkhahub/shared/src/lib/boot';
import { BootApp } from '@shikkhahub/shared/src/lib/boot';
import { AuthContextProvider } from '@shikkhahub/shared/src/contexts/AuthContext';
import { SettingsContextProvider } from '@shikkhahub/shared/src/contexts/SettingsContext';
import { useRefreshToken } from '@shikkhahub/shared/src/hooks/useRefreshToken';
import { AlertContextProvider } from '@shikkhahub/shared/src/contexts/AlertContext';
import { LogContextProvider } from '@shikkhahub/shared/src/contexts/LogContext';
import Toast from '@shikkhahub/shared/src/components/notifications/Toast';
import { RouterContext } from 'next/dist/shared/lib/router-context.shared-runtime';
import { AuthEvent } from '@shikkhahub/shared/src/lib/auth';
import { useError } from '@shikkhahub/shared/src/hooks/useError';
import {
  ExtensionMessageType,
  getCompanionWrapper,
} from '@shikkhahub/shared/src/lib/extension';
import { defaultQueryClientConfig } from '@shikkhahub/shared/src/lib/query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { PromptElement } from '@shikkhahub/shared/src/components/modals/Prompt';
import { GrowthBookProvider } from '@shikkhahub/shared/src/components/GrowthBookProvider';
import { NotificationsContextProvider } from '@shikkhahub/shared/src/contexts/NotificationsContext';
import { useEventListener } from '@shikkhahub/shared/src/hooks';
import { structuredCloneJsonPolyfill } from '@shikkhahub/shared/src/lib/structuredClone';
import Companion from './Companion';
import CustomRouter from '../lib/CustomRouter';
import { companionFetch } from './companionFetch';
import { version } from '../../package.json';

structuredCloneJsonPolyfill();

const queryClient = new QueryClient(defaultQueryClientConfig);
const router = new CustomRouter();

export type CompanionData = { url: string; deviceId: string } & Pick<
  Boot,
  | 'postData'
  | 'settings'
  | 'alerts'
  | 'user'
  | 'visit'
  | 'accessToken'
  | 'squads'
  | 'exp'
>;

const app = BootApp.Companion;

export default function App({
  deviceId,
  url,
  postData,
  settings,
  user,
  alerts,
  visit,
  accessToken,
  squads,
  exp,
}: CompanionData): ReactElement | null {
  useError();
  const [token, setToken] = useState(accessToken);
  const [isOptOutCompanion, setIsOptOutCompanion] = useState<boolean>(
    settings?.optOutCompanion ?? false,
  );

  const refetchData = async () => {
    if (isOptOutCompanion) {
      return undefined;
    }

    return browser.runtime.sendMessage({
      type: ExtensionMessageType.ContentLoaded,
    });
  };

  useRefreshToken(token, refetchData);

  useEventListener(globalThis as unknown as Window, 'message', async (e) => {
    if (e.data?.eventKey === AuthEvent.Login) {
      await refetchData();
    }
  });

  if (isOptOutCompanion || !postData) {
    return null;
  }

  return (
    <div>
      <style>
        @import &quot;{browser.runtime.getURL('css/companion.css')}&quot;;
      </style>
      <RouterContext.Provider value={router}>
        <QueryClientProvider client={queryClient}>
          <GrowthBookProvider
            app={app}
            user={user}
            deviceId={deviceId}
            experimentation={exp}
          >
            <AuthContextProvider
              user={user}
              visit={visit}
              tokenRefreshed
              getRedirectUri={() => browser.runtime.getURL('index.html')}
              updateUser={async () => undefined}
              squads={squads}
            >
              <SettingsContextProvider settings={settings}>
                <AlertContextProvider alerts={alerts}>
                  <LogContextProvider
                    app={app}
                    version={version}
                    fetchMethod={companionFetch}
                    backgroundMethod={(msg) => browser.runtime.sendMessage(msg)}
                    deviceId={deviceId}
                    getPage={() => url}
                  >
                    <NotificationsContextProvider
                      isNotificationsReady={false}
                      unreadCount={0}
                    >
                      <Companion
                        postData={postData}
                        companionHelper={alerts?.companionHelper ?? false}
                        companionExpanded={settings?.companionExpanded ?? false}
                        onOptOut={() => setIsOptOutCompanion(true)}
                        onUpdateToken={setToken}
                      />
                    </NotificationsContextProvider>
                    <PromptElement
                      parentSelector={() =>
                        getCompanionWrapper() ?? document.body
                      }
                    />
                    <Toast
                      autoDismissNotifications={
                        settings?.autoDismissNotifications
                      }
                    />
                  </LogContextProvider>
                </AlertContextProvider>
              </SettingsContextProvider>
            </AuthContextProvider>
          </GrowthBookProvider>
          <ReactQueryDevtools />
        </QueryClientProvider>
      </RouterContext.Provider>
    </div>
  );
}
