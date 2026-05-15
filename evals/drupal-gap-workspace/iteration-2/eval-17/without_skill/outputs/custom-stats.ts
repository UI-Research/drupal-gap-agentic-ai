import type { Core } from '@strapi/strapi';

async function statsHandler(ctx: any, strapi: Core.Strapi) {
  const published = await strapi.documents('api::article.article').count({
    status: 'published',
  });

  const draft = await strapi.documents('api::article.article').count({
    status: 'draft',
  });

  const byStatus = {
    published,
    draft,
  };

  ctx.send({
    byStatus,
    total: published + draft,
    timestamp: new Date().toISOString(),
  });
}

export default {
  routes: [
    {
      method: 'GET',
      path: '/api/v1/stats',
      handler: async (ctx: any) => {
        const strapiInstance = (global as any).strapi;
        await statsHandler(ctx, strapiInstance);
      },
      config: {
        policies: [],
        middlewares: [],
        auth: false,
      },
    },
  ],
};
