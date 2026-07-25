import browser from 'webextension-polyfill';
import { initialDataKey } from '@shikkhahub/shared/src/lib/constants';
import { ExtensionMessageType } from '@shikkhahub/shared/src/lib/extension';
import { gqlRequest } from '@shikkhahub/shared/src/graphql/common';
import { graphqlUrl } from '@shikkhahub/shared/src/lib/config';

const proxyRequest = {
  apply(_, __, args) {
    const { [initialDataKey]: initial, ...variables } = args?.[1];

    browser.runtime.sendMessage({
      type: ExtensionMessageType.GraphQLRequest,
      url: graphqlUrl,
      document: args?.[0],
      variables,
      headers: args?.[2],
    });

    return initial ?? null;
  },
};

export const companionRequest = new Proxy(gqlRequest, proxyRequest);
