import React, { useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from '@shikkhahub/shared/src/components/utilities/Link';
import { useAuthContext } from '@shikkhahub/shared/src/contexts/AuthContext';
import { useToastNotification } from '@shikkhahub/shared/src/hooks/useToastNotification';
import { useContentPreferenceStatusQuery } from '@shikkhahub/shared/src/hooks/contentPreference/useContentPreferenceStatusQuery';
import {
  ContentPreferenceStatus,
  ContentPreferenceType,
} from '@shikkhahub/shared/src/graphql/contentPreference';
import { useUserShortByIdQuery } from '@shikkhahub/shared/src/hooks/user/useUserShortByIdQuery';
import { useContentPreference } from '@shikkhahub/shared/src/hooks/contentPreference/useContentPreference';
import { ButtonSize } from '@shikkhahub/shared/src/components/buttons/common';
import {
  ProfileImageSize,
  ProfilePicture,
} from '@shikkhahub/shared/src/components/ProfilePicture';
import { Button } from '@shikkhahub/shared/src/components/buttons/Button';
import {
  Typography,
  TypographyTag,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';

const useSharedByToast = (): void => {
  const hasShownToast = useRef(false);
  const { user: currentUser, isAuthReady } = useAuthContext();
  const { query } = useRouter();
  const userId = (query?.userid as string) || null;
  const isSameUser = !!userId && userId === currentUser?.id;
  const { data: contentPreference, isPending } =
    useContentPreferenceStatusQuery({
      id: userId,
      entity: ContentPreferenceType.User,
    });
  const { data: user } = useUserShortByIdQuery({ id: userId });
  const { follow } = useContentPreference({ showToastOnSuccess: true });
  const { displayToast, dismissToast } = useToastNotification();
  const isDataReady = isAuthReady || (currentUser && !isPending);

  useEffect(() => {
    if (
      !user ||
      isSameUser ||
      !isDataReady ||
      hasShownToast.current ||
      contentPreference?.status === ContentPreferenceStatus.Blocked
    ) {
      return undefined;
    }

    const showFollow =
      !!currentUser &&
      ![
        ContentPreferenceStatus.Follow,
        ContentPreferenceStatus.Subscribed,
      ].includes(contentPreference?.status);

    const timeout = setTimeout(() => {
      hasShownToast.current = true;
      displayToast(
        <div className="flex items-center gap-4">
          <Link href={`/${user.username}`}>
            <a className="flex items-center gap-2">
              <ProfilePicture user={user} size={ProfileImageSize.Medium} />
              <span>
                <Typography
                  type={TypographyType.Subhead}
                  tag={TypographyTag.Span}
                  bold
                >
                  {user.name}
                </Typography>{' '}
                <Typography
                  type={TypographyType.Subhead}
                  tag={TypographyTag.Span}
                >
                  shared this post
                </Typography>
              </span>
            </a>
          </Link>
          {showFollow && (
            <Button
              onClick={() => {
                follow({
                  entity: ContentPreferenceType.User,
                  id: user?.id,
                  entityName: `@${user.username}`,
                });
              }}
              className="bg-background-default text-text-primary"
              size={ButtonSize.Small}
            >
              Follow
            </Button>
          )}
        </div>,
      );
      // Set a small timeout to ensure its shown after the page is loaded and won't be cleared by updates.
    }, 100);

    return () => clearTimeout(timeout);
  }, [
    user,
    contentPreference?.status,
    hasShownToast,
    displayToast,
    dismissToast,
    follow,
    isSameUser,
    isDataReady,
    currentUser,
  ]);
};

export default useSharedByToast;
