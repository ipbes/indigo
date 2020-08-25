# -*- encoding: utf-8 -*-
# stub: slaw 10.1.0 ruby lib

Gem::Specification.new do |s|
  s.name = "slaw".freeze
  s.version = "10.1.0"

  s.required_rubygems_version = Gem::Requirement.new(">= 0".freeze) if s.respond_to? :required_rubygems_version=
  s.require_paths = ["lib".freeze]
  s.authors = ["Greg Kempe".freeze]
  s.date = "2020-06-18"
  s.description = "Slaw is a lightweight library for rendering and generating Akoma Ntoso acts from plain text and PDF documents.".freeze
  s.email = ["greg@kempe.net".freeze]
  s.executables = ["slaw".freeze]
  s.files = ["bin/slaw".freeze]
  s.homepage = "https://github.com/longhotsummer/slaw".freeze
  s.licenses = ["MIT".freeze]
  s.rubygems_version = "3.1.2".freeze
  s.summary = "A lightweight library for using Akoma Ntoso acts in Ruby.".freeze

  s.installed_by_version = "3.1.2" if s.respond_to? :installed_by_version

  if s.respond_to? :specification_version then
    s.specification_version = 4
  end

  if s.respond_to? :add_runtime_dependency then
    s.add_development_dependency(%q<rake>.freeze, ["~> 12.3"])
    s.add_development_dependency(%q<rspec>.freeze, ["~> 3.8"])
    s.add_runtime_dependency(%q<nokogiri>.freeze, ["~> 1.8"])
    s.add_runtime_dependency(%q<treetop>.freeze, ["~> 1.5"])
    s.add_runtime_dependency(%q<log4r>.freeze, ["~> 1.1"])
    s.add_runtime_dependency(%q<thor>.freeze, ["~> 0.20"])
    s.add_runtime_dependency(%q<mimemagic>.freeze, ["~> 0.2"])
  else
    s.add_dependency(%q<rake>.freeze, ["~> 12.3"])
    s.add_dependency(%q<rspec>.freeze, ["~> 3.8"])
    s.add_dependency(%q<nokogiri>.freeze, ["~> 1.8"])
    s.add_dependency(%q<treetop>.freeze, ["~> 1.5"])
    s.add_dependency(%q<log4r>.freeze, ["~> 1.1"])
    s.add_dependency(%q<thor>.freeze, ["~> 0.20"])
    s.add_dependency(%q<mimemagic>.freeze, ["~> 0.2"])
  end
end
