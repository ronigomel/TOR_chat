import pygame


class Message:
    def __init__(self, sent: bool, text: str, img_file: str, placement: tuple):
        self.sent = sent
        self.text = text
        self.img_file = img_file
        self.img = pygame.image.load(self.img_file)
        self.placement = placement
        self.seen = True

    def get_seen(self):
        return self.seen

    def get_placement(self):
        return self.placement

    def print(self, screen):
        red = (255, 0, 0, 0)
        self.img = pygame.image.load(self.img_file).convert()
        self.img.set_colorkey(red)
        screen.blit(self.img, self.placement)
        self.print_txt(screen)
        #pygame.display.flip()

    def print_txt(self, screen):
        font = pygame.font.Font(None, 25)
        txt = font.render(self.text, True, (0, 0, 0, 0), (173, 113, 89, 0))
        txt_rect = txt.get_rect()
        txt_rect.center = (self.placement[0]+55, self.placement[1]+32)
        screen.blit(txt, txt_rect)

    def set_placement(self, placement):
        self.placement = placement

    def delete(self, screen):
        hide = pygame.image.load('media/hide.jpg')
        screen.blit(hide, (self.placement[0], self.placement[1]+102))
        pygame.display.update()

    def get_text(self):
        return self.text

    def erase(self):
        self.seen = False