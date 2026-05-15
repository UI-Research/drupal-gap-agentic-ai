import type { Core } from '@strapi/strapi';

export default ({ strapi }: { strapi: Core.Strapi }) => ({
  async get(ctx) {
    const store = strapi.store({ type: 'core', name: 'banner_settings' });
    const banner_message = await store.get({ key: 'banner_message' });
    ctx.send({ banner_message });
  },

  async update(ctx) {
    const { banner_message } = ctx.request.body as { banner_message: string };
    const store = strapi.store({ type: 'core', name: 'banner_settings' });
    await store.set({ key: 'banner_message', value: banner_message });
    ctx.send({ banner_message });
  },
});
