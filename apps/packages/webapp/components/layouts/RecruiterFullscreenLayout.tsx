import type { ReactNode } from 'react';
import React, { useContext } from 'react';
import { InAppNotificationElement } from '@shikkhahub/shared/src/components/notifications/InAppNotification';
import { PromptElement } from '@shikkhahub/shared/src/components/modals/Prompt';
import Toast from '@shikkhahub/shared/src/components/notifications/Toast';
import SettingsContext from '@shikkhahub/shared/src/contexts/SettingsContext';
import { PendingSubmissionProvider } from '@shikkhahub/shared/src/features/opportunity/context/PendingSubmissionContext';
import { ErrorBoundary } from '@shikkhahub/shared/src/components/ErrorBoundary';
import RecruiterErrorFallback from '@shikkhahub/shared/src/components/errors/RecruiterErrorFallback';
import { useRecruiterLayoutReady } from '@shikkhahub/shared/src/hooks/useRecruiterLayoutReady';
import { useIntercom } from '../../hooks/useIntercom';
import { recruiterSeo } from '../../next-seo';

const RecruiterFullscreenLayoutInner = ({
  children,
}: {
  children: ReactNode;
}) => {
  const { autoDismissNotifications } = useContext(SettingsContext);
  const { isPageReady } = useRecruiterLayoutReady();

  useIntercom();

  if (!isPageReady) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col antialiased">
      <InAppNotificationElement />
      <PromptElement />
      <Toast autoDismissNotifications={autoDismissNotifications} />
      <ErrorBoundary
        feature="recruiter-self-serve"
        fallback={<RecruiterErrorFallback />}
      >
        {children}
      </ErrorBoundary>
    </div>
  );
};

const GetLayout = (page: ReactNode): ReactNode => {
  return (
    <PendingSubmissionProvider>
      <RecruiterFullscreenLayoutInner>{page}</RecruiterFullscreenLayoutInner>
    </PendingSubmissionProvider>
  );
};

export { GetLayout as getLayout };

export const layoutProps = { seo: recruiterSeo };
