<?php

namespace Drupal\auto_slug\EventSubscriber;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\node\NodeInterface;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\KernelEvents;

/**
 * Subscribes to kernel events for auto slug generation.
 */
class AutoSlugSubscriber implements EventSubscriberInterface {

  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
  ) {}

  /**
   * {@inheritdoc}
   */
  public static function getSubscribedEvents(): array {
    return [
      KernelEvents::REQUEST => ['onKernelRequest', 0],
    ];
  }

  /**
   * Handles kernel request events.
   */
  public function onKernelRequest(RequestEvent $event): void {
    // Slug generation is handled via hook_node_presave().
    // This subscriber exists to allow dependency injection and testability.
  }

  /**
   * Generates a slug from a node title.
   */
  public function generateSlug(NodeInterface $node): string {
    $title = $node->getTitle() ?? '';
    return trim(mb_strtolower(preg_replace('/[^a-z0-9]+/i', '-', $title)), '-');
  }

}
