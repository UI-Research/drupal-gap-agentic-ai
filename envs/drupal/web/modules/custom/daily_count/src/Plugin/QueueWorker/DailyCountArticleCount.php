<?php

declare(strict_types=1);

namespace Drupal\daily_count\Plugin\QueueWorker;

use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Queue\QueueWorkerBase;
use Drupal\daily_count\Service\ArticleCounter;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Processes the daily article count queue item.
 *
 * @QueueWorker(
 *   id = "daily_count_article_count",
 *   title = @Translation("Daily Article Count"),
 *   cron = {"time" = 30}
 * )
 */
class DailyCountArticleCount extends QueueWorkerBase implements ContainerFactoryPluginInterface {

  /**
   * The article counter service.
   */
  protected ArticleCounter $articleCounter;

  /**
   * Constructs a DailyCountArticleCount queue worker.
   *
   * @param array $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   The plugin ID.
   * @param mixed $plugin_definition
   *   The plugin definition.
   * @param \Drupal\daily_count\Service\ArticleCounter $article_counter
   *   The article counter service.
   */
  public function __construct(
    array $configuration,
    $plugin_id,
    $plugin_definition,
    ArticleCounter $article_counter,
  ) {
    parent::__construct($configuration, $plugin_id, $plugin_definition);
    $this->articleCounter = $article_counter;
  }

  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container, array $configuration, $plugin_id, $plugin_definition): static {
    return new static(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $container->get('daily_count.article_counter'),
    );
  }

  /**
   * {@inheritdoc}
   */
  public function processItem($data): void {
    $this->articleCounter->countAndLog();
  }

}
