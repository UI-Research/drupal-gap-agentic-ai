<?php

declare(strict_types=1);

namespace Drupal\daily_count\Service;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Psr\Log\LoggerInterface;

/**
 * Counts published Article nodes and logs the result.
 */
class ArticleCounter {

  /**
   * The entity type manager.
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * The logger.
   */
  protected LoggerInterface $logger;

  /**
   * Constructs an ArticleCounter service.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entity_type_manager
   *   The entity type manager.
   * @param \Drupal\Core\Logger\LoggerChannelFactoryInterface $logger_factory
   *   The logger channel factory.
   */
  public function __construct(
    EntityTypeManagerInterface $entity_type_manager,
    $logger_factory,
  ) {
    $this->entityTypeManager = $entity_type_manager;
    $this->logger = $logger_factory->get('daily_count');
  }

  /**
   * Counts published Article nodes and logs the total.
   *
   * @return int
   *   The number of published Article nodes.
   */
  public function countAndLog(): int {
    $storage = $this->entityTypeManager->getStorage('node');
    $count = (int) $storage->getQuery()
      ->accessCheck(FALSE)
      ->condition('type', 'article')
      ->condition('status', 1)
      ->count()
      ->execute();

    $this->logger->info('Daily count: @count published Article nodes.', [
      '@count' => $count,
    ]);

    return $count;
  }

}
