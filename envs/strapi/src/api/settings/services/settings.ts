import type { Core } from '@strapi/strapi';

export default ({ strapi }: { strapi: Core.Strapi }) => ({
  async getBannerMessage(): Promise<string> {
    const store = strapi.store({ type: 'core', name: 'banner_settings' });
    const value = await store.get({ key: 'banner_message' });
    return (value as string) || 'Welcome!';
  },
});
