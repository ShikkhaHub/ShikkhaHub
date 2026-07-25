import type { ReactElement } from 'react';
import React from 'react';
import {
  Button,
  ButtonSize,
  ButtonVariant,
} from '@shikkhahub/shared/src/components/buttons/Button';
import { PlusIcon } from '@shikkhahub/shared/src/components/icons';
import type { NextSeoProps } from 'next-seo';
import { UserExperienceType } from '@shikkhahub/shared/src/graphql/user/profile';
import { ExperienceSettings } from '@shikkhahub/shared/src/components/profile/ExperienceSettings';
import Link from '@shikkhahub/shared/src/components/utilities/Link';
import { webappUrl } from '@shikkhahub/shared/src/lib/constants';
import { getPageSeoTitles } from '../../../../components/layouts/utils';
import { defaultSeo } from '../../../../next-seo';
import { getSettingsLayout } from '../../../../components/layouts/SettingsLayout';
import { AccountPageContainer } from '../../../../components/layouts/SettingsLayout/AccountPageContainer';

const seo: NextSeoProps = {
  ...defaultSeo,
  ...getPageSeoTitles('Open Source'),
};

const OpenSourcePage = (): ReactElement => {
  return (
    <AccountPageContainer
      title="Open source"
      actions={
        <Link
          href={`${webappUrl}settings/profile/experience/edit?type=${UserExperienceType.OpenSource}`}
        >
          <Button
            variant={ButtonVariant.Subtle}
            size={ButtonSize.Small}
            icon={<PlusIcon />}
          >
            Add
          </Button>
        </Link>
      }
    >
      <ExperienceSettings
        experienceType={UserExperienceType.OpenSource}
        emptyStateMessage="No open source contributions added yet"
      />
    </AccountPageContainer>
  );
};

OpenSourcePage.getLayout = getSettingsLayout;
OpenSourcePage.layoutProps = { seo };

export default OpenSourcePage;
