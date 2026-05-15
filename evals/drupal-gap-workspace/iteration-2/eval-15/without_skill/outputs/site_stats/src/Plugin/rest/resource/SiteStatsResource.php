<?php

namespace Drupal\site_stats\Plugin\rest\resource;

use Drupal\rest\Attribute\RestResource;
use Drupal\rest\Plugin\ResourceBase;
use Drupal\rest\ResourceResponse;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Psr\Log\LoggerInterface;
use Symfony\Component\DependencyInjection\ContainerInterface;

#[RestResource(
  id: "site_stats_resource",
  label: new TranslatableMarkup("Site Stats Resource"),
  uri_paths: [
    "canonical" => "/api/site-stats",
  ]
)]
class SiteStatsResource extends ResourceBase {

  public function get(): ResourceResponse {
    $article_count = \Drupal::entityQuery('node')
      ->condition('type', 'article')
      ->condition('status', 1)
      ->accessCheck(FALSE)
      ->count()
      ->execute();

    $user_count = \Drupal::entityQuery('user')
      ->condition('status', 1)
      ->accessCheck(FALSE)
      ->count()
      ->execute();

    $data = [
      'published_articles' => (int) $article_count,
      'active_users' => (int) $user_count,
      'timestamp' => \Drupal::time()->getRequestTime(),
    ];

    $response = new ResourceResponse($data);
    $response->addCacheableDependency(['#cache' => ['max-age' => 300]]);

    return $response;
  }

}
