# Makefile for setting up Next.js project with pnpm

# Variables
APP_NAME ?= my-app
NODE_VERSION ?= 20.15.0  # Change this to your required Node.js version

.PHONY: all setup install-deps run-dev clean

all: setup install-deps

# Target to set up a new Next.js app using pnpm
setup:
	@npx create-next-app@15.2.3 $(APP_NAME) --typescript --package-manager pnpm
	@cd $(APP_NAME) && pnpm dlx shadcn@latest init

# Target to install all dependencies using pnpm
install-deps:
	@cd $(APP_NAME) && \
	pnpm add ai @ai-sdk/openai lucide-react react@18 react-dom@18 react-markdown remark-gfm react-syntax-highlighter next-themes @clerk/nextjs yet-another-react-lightbox @headlessui/react && \
	pnpm add -D @types/react-syntax-highlighter && \
	pnpm dlx shadcn@latest add card input scroll-area && \
	pnpm dlx shadcn@latest add https://tailark.com/r/hero-section-4.json && \
	pnpm dlx shadcn@latest add https://tailark.com/r/features-2.json && \
	pnpm dlx shadcn@latest add https://tailark.com/r/footer-1.json && \
	pnpm dlx shadcn@latest add https://tailark.com/r/content-1.json && \
	pnpm dlx shadcn@latest add https://tailark.com/r/pricing-1.json && \
	pnpm dlx shadcn@latest add https://tailark.com/r/team-1.json

# Target to start the development server using pnpm
run-dev:
	@cd $(APP_NAME) && pnpm run dev

# Clean the project directory
clean:
	@rm -rf $(APP_NAME)
