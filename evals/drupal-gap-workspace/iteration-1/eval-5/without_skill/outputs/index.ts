export default {
  register() {},

  async bootstrap({ strapi }) {
    // Set public permissions for Article
    const publicRole = await strapi.db.query('plugin::users-permissions.role').findOne({
      where: { type: 'public' },
    });

    if (publicRole) {
      const permissions = await strapi.db.query('plugin::users-permissions.permission').findMany({
        where: {
          role: publicRole.id,
          action: {
            $in: ['api::article.article.find', 'api::article.article.findOne'],
          },
        },
      });

      for (const action of ['api::article.article.find', 'api::article.article.findOne']) {
        const exists = permissions.find((p) => p.action === action);
        if (!exists) {
          await strapi.db.query('plugin::users-permissions.permission').create({
            data: { action, role: publicRole.id, enabled: true },
          });
        }
      }
    }

    // Seed an article if none exist
    const count = await strapi.db.query('api::article.article').count();
    if (count === 0) {
      await strapi.documents('api::article.article').create({
        data: {
          title: 'Benchmark baseline',
          slug: 'benchmark-baseline',
          body: 'Test article for benchmarking.',
        },
        status: 'published',
      });
    }
  },
};
