import type { ReactElement } from 'react';
import React, { useMemo, useRef } from 'react';
import {
  ReferralCampaignKey,
  usePlusSubscription,
  useReferralCampaign,
} from '@shikkhahub/shared/src/hooks';
import { link } from '@shikkhahub/shared/src/lib/links';
import { labels } from '@shikkhahub/shared/src/lib';
import {
  generateQueryKey,
  getNextPageParam,
  RequestKey,
} from '@shikkhahub/shared/src/lib/query';
import { useAuthContext } from '@shikkhahub/shared/src/contexts/AuthContext';
import { REFERRED_USERS_QUERY } from '@shikkhahub/shared/src/graphql/users';
import UserList from '@shikkhahub/shared/src/components/profile/UserList';
import { checkFetchMore } from '@shikkhahub/shared/src/components/containers/InfiniteScrolling';
import type { ReferredUsersData } from '@shikkhahub/shared/src/graphql/common';
import { gqlClient } from '@shikkhahub/shared/src/graphql/common';
import { SocialShareList } from '@shikkhahub/shared/src/components/widgets/SocialShareList';
import { Separator } from '@shikkhahub/shared/src/components/cards/common/common';
import type { UserShortProfile } from '@shikkhahub/shared/src/lib/user';
import { format } from 'date-fns';
import { IconSize } from '@shikkhahub/shared/src/components/Icon';
import { useInfiniteQuery } from '@tanstack/react-query';
import {
  LogEvent,
  TargetId,
  TargetType,
} from '@shikkhahub/shared/src/lib/log';
import type { ShareProvider } from '@shikkhahub/shared/src/lib/share';
import { useShareOrCopyLink } from '@shikkhahub/shared/src/hooks/useShareOrCopyLink';
import { InviteLinkInput } from '@shikkhahub/shared/src/components/referral';
import { TruncateText } from '@shikkhahub/shared/src/components/utilities';
import type { NextSeoProps } from 'next-seo';
import {
  Typography,
  TypographyColor,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';
import {
  Button,
  ButtonColor,
  ButtonVariant,
} from '@shikkhahub/shared/src/components/buttons/Button';
import { useLazyModal } from '@shikkhahub/shared/src/hooks/useLazyModal';
import { LazyModal } from '@shikkhahub/shared/src/components/modals/common/types';
import { useLogContext } from '@shikkhahub/shared/src/contexts/LogContext';
import { PlusUser } from '@shikkhahub/shared/src/components/PlusUser';
import { GiftIcon, InviteIcon } from '@shikkhahub/shared/src/components/icons';
import AccountContentSection from '../../components/layouts/SettingsLayout/AccountContentSection';
import { AccountPageContainer } from '../../components/layouts/SettingsLayout/AccountPageContainer';
import { getSettingsLayout } from '../../components/layouts/SettingsLayout';
import { defaultSeo } from '../../next-seo';
import { getPageSeoTitles } from '../../components/layouts/utils';

const seo: NextSeoProps = {
  ...defaultSeo,
  ...getPageSeoTitles('Invite Friends'),
};

const AccountInvitePage = (): ReactElement => {
  const { openModal } = useLazyModal();
  const { user } = useAuthContext();
  const container = useRef<HTMLDivElement>();
  const referredKey = generateQueryKey(RequestKey.ReferredUsers, user);
  const { url, referredUsersCount } = useReferralCampaign({
    campaignKey: ReferralCampaignKey.Generic,
  });
  const { isValidRegion: isPlusAvailable } = useAuthContext();
  const { logSubscriptionEvent } = usePlusSubscription();
  const { logEvent } = useLogContext();
  const inviteLink = url || link.referral.defaultUrl;
  const [, onShareOrCopyLink] = useShareOrCopyLink({
    text: labels.referral.generic.inviteText,
    link: inviteLink,
    logObject: () => ({
      event_name: LogEvent.CopyReferralLink,
      target_id: TargetId.InviteFriendsPage,
    }),
  });
  const usersResult = useInfiniteQuery<ReferredUsersData>({
    queryKey: referredKey,
    queryFn: ({ pageParam }) =>
      gqlClient.request(REFERRED_USERS_QUERY, {
        after: typeof pageParam === 'string' ? pageParam : undefined,
      }),
    initialPageParam: '',
    getNextPageParam: ({ referredUsers }) =>
      getNextPageParam(referredUsers?.pageInfo),
  });
  const users: UserShortProfile[] = useMemo(() => {
    const list: UserShortProfile[] = [];
    usersResult.data?.pages.forEach((page) => {
      page?.referredUsers.edges.forEach(({ node }) => {
        list.push(node as UserShortProfile);
      });
    }, []);

    return list;
  }, [usersResult]);

  const onLogShare = (provider: ShareProvider) => {
    logEvent({
      event_name: LogEvent.InviteReferral,
      target_id: provider,
      target_type: TargetType.InviteFriendsPage,
    });
  };

  return (
    <AccountPageContainer title="Invite friends">
      {isPlusAvailable && (
        <div className="mb-6 flex flex-col gap-4">
          <div className="space-y-1">
            <div className="flex gap-1">
              <Typography type={TypographyType.Body} bold>
                Gift daily.dev Plus
              </Typography>
              <PlusUser iconSize={IconSize.XSmall} withText={false} />
            </div>
            <Typography
              className="border-plus"
              color={TypographyColor.Tertiary}
              type={TypographyType.Callout}
            >
              Gifting daily.dev Plus to a friend is the ultimate way to say,
              &apos;I&apos;ve got your back.&apos; It unlocks an ad-free
              experience, advanced content filtering and customizations, plus AI
              superpowers to supercharge their daily.dev journey.
            </Typography>
          </div>
          <Button
            icon={<GiftIcon size={IconSize.Small} secondary />}
            variant={ButtonVariant.Secondary}
            color={ButtonColor.Bacon}
            onClick={() => {
              logSubscriptionEvent({
                event_name: LogEvent.GiftSubscription,
                target_id: TargetId.InviteFriendsPage,
              });
              openModal({
                type: LazyModal.GiftPlus,
              });
            }}
            className="max-w-fit border-action-plus-default text-action-plus-default"
          >
            Buy as gift
          </Button>
        </div>
      )}
      <InviteLinkInput
        link={inviteLink}
        logProps={{
          event_name: LogEvent.CopyReferralLink,
          target_id: TargetId.InviteFriendsPage,
        }}
      />
      <span className="my-4 p-0.5 font-bold text-text-tertiary typo-callout">
        or invite via
      </span>
      <div className="flex flex-row flex-wrap gap-2 gap-y-4">
        <SocialShareList
          link={inviteLink}
          description={labels.referral.generic.inviteText}
          onNativeShare={onShareOrCopyLink}
          onClickSocial={onLogShare}
          shortenUrl={false}
        />
      </div>
      <AccountContentSection
        title="Your referrals"
        description="Developers who joined through your invite link"
      >
        <UserList
          users={users}
          isLoading={usersResult?.isLoading}
          scrollingProps={{
            isFetchingNextPage: usersResult.isFetchingNextPage,
            canFetchMore: checkFetchMore(usersResult),
            fetchNextPage: usersResult.fetchNextPage,
            className: 'mt-4',
          }}
          emptyPlaceholder={
            <div className="mt-16 flex flex-col items-center text-text-secondary">
              <InviteIcon size={IconSize.XXXLarge} />
              <p className="mt-2 typo-body">
                No one has joined yet. Share your link!
              </p>
            </div>
          }
          userInfoProps={{
            scrollingContainer: container.current,
            className: {
              container: 'px-0 py-3 items-center',
              textWrapper: 'flex-none',
            },
            transformUsername({
              username,
              createdAt,
            }: UserShortProfile): React.ReactNode {
              return (
                <span className="flex text-text-secondary typo-callout">
                  <TruncateText>@{username}</TruncateText>
                  <Separator />
                  <time dateTime={createdAt}>
                    {format(new Date(createdAt), 'dd MMM yyyy')}
                  </time>
                </span>
              );
            },
          }}
          placeholderAmount={referredUsersCount}
        />
      </AccountContentSection>
    </AccountPageContainer>
  );
};

AccountInvitePage.getLayout = getSettingsLayout;
AccountInvitePage.layoutProps = { seo };

export default AccountInvitePage;
