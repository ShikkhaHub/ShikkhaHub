import React from 'react';
import type { ReactElement } from 'react';
import type { NextSeoProps } from 'next-seo';

import {
  Typography,
  TypographyColor,
  TypographyTag,
  TypographyType,
} from '@shikkhahub/shared/src/components/typography/Typography';

import Link from '@shikkhahub/shared/src/components/utilities/Link';
import {
  plusOrganizationInfo,
  plusUrl,
} from '@shikkhahub/shared/src/lib/constants';
import {
  Button,
  ButtonSize,
  ButtonVariant,
} from '@shikkhahub/shared/src/components/buttons/Button';
import {
  getRoleName,
  HorizontalSeparator,
} from '@shikkhahub/shared/src/components/utilities';
import {
  ArrowIcon,
  OrganizationIcon,
} from '@shikkhahub/shared/src/components/icons';
import { IconSize } from '@shikkhahub/shared/src/components/Icon';
import { InviteLinkInput } from '@shikkhahub/shared/src/components/referral';
import { LogEvent, TargetId } from '@shikkhahub/shared/src/lib/log';
import {
  ReferralCampaignKey,
  useReferralCampaign,
} from '@shikkhahub/shared/src/hooks';
import { link } from '@shikkhahub/shared/src/lib';
import { useOrganizations } from '@shikkhahub/shared/src/features/organizations/hooks/useOrganizations';

import {
  Image,
  ImageType,
} from '@shikkhahub/shared/src/components/image/Image';
import UserBadge from '@shikkhahub/shared/src/components/UserBadge';
import { getOrganizationSettingsUrl } from '@shikkhahub/shared/src/features/organizations/utils';
import { AccountPageContainer } from '../../../components/layouts/SettingsLayout/AccountPageContainer';
import { getSettingsLayout } from '../../../components/layouts/SettingsLayout';
import { defaultSeo } from '../../../next-seo';
import { getPageSeoTitles } from '../../../components/layouts/utils';

const NoOrganizations = () => {
  const { url } = useReferralCampaign({
    campaignKey: ReferralCampaignKey.Generic,
  });
  const inviteLink = url || link.referral.defaultUrl;

  return (
    <div className="flex flex-col gap-1 pt-6">
      <OrganizationIcon
        size={IconSize.XXXLarge}
        className="self-center text-text-tertiary"
      />

      <Typography bold center type={TypographyType.Title2}>
        No organization yet?
      </Typography>

      <Typography
        center
        type={TypographyType.Callout}
        color={TypographyColor.Secondary}
      >
        Ask your manager to create an organization and invite the team. Use the
        link below to make it easy. If you&apos;re lucky, they&apos;ll cover the
        cost too and you&apos;ll look like a hero for bringing it up.
      </Typography>

      <InviteLinkInput
        link={inviteLink}
        logProps={{
          event_name: LogEvent.CopyReferralLink,
          target_id: TargetId.OrganizationsPage,
        }}
        className={{ container: 'mt-6' }}
      />
    </div>
  );
};

const Page = (): ReactElement => {
  const { organizations, isFetching } = useOrganizations();

  return (
    <AccountPageContainer
      title="Organizations"
      className={{ container: 'overflow-hidden', section: 'gap-6' }}
    >
      <section className="flex flex-col gap-2">
        <Typography
          type={TypographyType.Callout}
          color={TypographyColor.Secondary}
        >
          Organizations let your team unlock the full power of daily.dev Plus
          together including premium features, shared learning, and streamlined
          user management, all in one place. Create an organization using your
          company, team, or community name.
        </Typography>

        <Link href={plusOrganizationInfo} passHref>
          <Typography
            tag={TypographyTag.Link}
            type={TypographyType.Callout}
            color={TypographyColor.Link}
          >
            Learn more about organizations at daily.dev →
          </Typography>
        </Link>
      </section>

      <Link href={`${plusUrl}?type=team`} passHref>
        <Button
          variant={ButtonVariant.Primary}
          size={ButtonSize.Small}
          className="self-start"
        >
          New organization
        </Button>
      </Link>

      <HorizontalSeparator />

      <section className="flex flex-col">
        <Typography bold type={TypographyType.Title3}>
          Your organizations
        </Typography>

        {organizations && organizations.length > 0 ? (
          <div className="flex flex-col gap-4 pt-4">
            {organizations.map(({ role, organization }) => (
              <Link
                key={organization.id}
                href={getOrganizationSettingsUrl(organization.id, 'members')}
                passHref
              >
                <a className="flex items-center gap-2">
                  <Image
                    className="mr-2 size-8 rounded-full object-cover"
                    src={organization.image}
                    alt={`Avatar of ${organization.name}`}
                    type={ImageType.Organization}
                  />

                  <Typography bold truncate type={TypographyType.Callout}>
                    {organization.name}
                  </Typography>

                  <UserBadge role={role} className="mt-0.5">
                    {getRoleName(role)}
                  </UserBadge>

                  <ArrowIcon
                    size={IconSize.Small}
                    className="ml-auto rotate-90 text-text-tertiary"
                  />
                </a>
              </Link>
            ))}
          </div>
        ) : (
          !isFetching && <NoOrganizations />
        )}
      </section>
    </AccountPageContainer>
  );
};

const seo: NextSeoProps = {
  ...defaultSeo,
  ...getPageSeoTitles('Organizations'),
};

Page.getLayout = getSettingsLayout;
Page.layoutProps = { seo };

export default Page;
